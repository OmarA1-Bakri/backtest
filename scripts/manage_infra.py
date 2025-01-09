#!/usr/bin/env python3
"""Infrastructure management script."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )
    return result


def init_terraform(env, region):
    """Initialize Terraform with correct backend configuration."""
    backend_config = {
        "bucket": f"backtest-terraform-state-{env}",
        "key": f"{env}/terraform.tfstate",
        "region": region,
        "encrypt": True,
        "dynamodb_table": "terraform-lock",
    }

    # Create backend config file
    with open("backend.hcl", "w") as f:
        for key, value in backend_config.items():
            f.write(f'{key} = "{value}"\n')

    result = run_command(
        "terraform init -backend-config=backend.hcl", cwd="infra/terraform"
    )

    if result.returncode != 0:
        print("Terraform init failed:", result.stderr)
        return False

    return True


def validate_terraform():
    """Validate Terraform configuration."""
    result = run_command("terraform validate", cwd="infra/terraform")
    if result.returncode != 0:
        print("Terraform validation failed:", result.stderr)
        return False

    return True


def plan_terraform(env, vars_file):
    """Generate and show Terraform plan."""
    cmd = f"terraform plan -var-file={vars_file} -var='environment={env}' -out=tfplan"
    result = run_command(cmd, cwd="infra/terraform")

    if result.returncode != 0:
        print("Terraform plan failed:", result.stderr)
        return False

    return True


def apply_terraform():
    """Apply Terraform plan."""
    result = run_command("terraform apply tfplan", cwd="infra/terraform")
    if result.returncode != 0:
        print("Terraform apply failed:", result.stderr)
        return False

    return True


def get_current_state():
    """Get current infrastructure state."""
    result = run_command("terraform show -json", cwd="infra/terraform")

    if result.returncode != 0:
        print("Failed to get current state:", result.stderr)
        return None

    return json.loads(result.stdout)


def validate_changes(current_state, env):
    """Validate proposed changes against current state."""
    # Add custom validation logic here
    # For example, prevent destructive changes in production
    if env == "production":
        # Check for resource deletions
        if "resource_changes" in current_state:
            for change in current_state["resource_changes"]:
                if change["change"]["actions"] == ["delete"]:
                    print(f"Error: Destructive change detected for {change['address']}")
                    return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Infrastructure management tool")
    parser.add_argument("action", choices=["init", "validate", "plan", "apply"])
    parser.add_argument("--env", required=True, help="Environment (staging/production)")
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--vars-file", help="Terraform variables file")
    args = parser.parse_args()

    if args.action == "init":
        success = init_terraform(args.env, args.region)
    elif args.action == "validate":
        success = validate_terraform()
    elif args.action == "plan":
        if not args.vars_file:
            print("Error: --vars-file required for plan action")
            sys.exit(1)
        success = plan_terraform(args.env, args.vars_file)
    elif args.action == "apply":
        current_state = get_current_state()
        if current_state and validate_changes(current_state, args.env):
            success = apply_terraform()
        else:
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
