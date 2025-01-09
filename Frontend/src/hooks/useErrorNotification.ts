import { useSnackbar } from 'notistack';
import { ApiError, createErrorMessage } from '../utils/errorHandler';

export const useErrorNotification = () => {
  const { enqueueSnackbar } = useSnackbar();

  const showError = (error: ApiError) => {
    const message = createErrorMessage(error);
    
    enqueueSnackbar(message, {
      variant: 'error',
      autoHideDuration: 5000,
      anchorOrigin: {
        vertical: 'top',
        horizontal: 'right',
      },
    });
  };

  return { showError };
};
