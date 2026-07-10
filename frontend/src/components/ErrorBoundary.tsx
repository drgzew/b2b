import React from 'react';
import { Button, Result } from 'antd';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

// Ловит ошибки рендера, чтобы вместо белого экрана показать понятный экран
// с возможностью перезагрузки (пункт «не белый экран» из задач по кабинету).
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    console.error('Необработанная ошибка интерфейса:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Что-то пошло не так"
          subTitle="Произошла ошибка в интерфейсе. Попробуйте перезагрузить страницу."
          extra={
            <Button
              type="primary"
              style={{ background: '#00AEEF' }}
              onClick={() => window.location.reload()}
            >
              Перезагрузить
            </Button>
          }
        />
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
