import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders see the GH PR link', () => {
  const { getByText } = render(<App />);
  const linkElement = getByText(/Rules under specification/i);
  expect(linkElement).toBeInTheDocument();
});
