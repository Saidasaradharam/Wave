import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AuthForms from '../src/components/AuthForms';
import * as api from '../src/services/api';

// Mock the API calls
jest.mock('../src/services/api');

describe('Authentication Forms', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders login form by default', () => {
    render(<AuthForms onAuthSuccess={() => {}} />);
    expect(screen.getByText('Welcome Back')).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/^name$/i)).not.toBeInTheDocument();
  });

  test('switches to register form', () => {
    render(<AuthForms onAuthSuccess={() => {}} />);
    fireEvent.click(screen.getByText(/sign up/i));
    
    expect(screen.getByText('Create Account')).toBeInTheDocument();
    expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
  });

  test('submits login form with valid data', async () => {
    const mockOnAuthSuccess = jest.fn();
    api.login.mockResolvedValueOnce({
      access_token: 'fake-token',
      user: { id: 1, email: 'test@test.com' }
    });

    render(<AuthForms onAuthSuccess={mockOnAuthSuccess} />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    });
    
    fireEvent.click(screen.getByRole('button', { name: /submit login form/i }));
    
    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith('test@test.com', 'password123');
      expect(mockOnAuthSuccess).toHaveBeenCalledWith({ id: 1, email: 'test@test.com' });
    });
  });

  test('shows error message on failure', async () => {
    api.login.mockRejectedValueOnce({
      response: { data: { detail: 'Invalid credentials' } }
    });

    render(<AuthForms onAuthSuccess={() => {}} />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'wrong@test.com' }
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrong' }
    });
    
    fireEvent.click(screen.getByRole('button', { name: /submit login form/i }));
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials');
    });
  });
});
