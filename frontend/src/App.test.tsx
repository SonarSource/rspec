import React from 'react';
import { render } from '@testing-library/react';
import App from './App';

test('renders see the GH PR link', () => {
  const { getByText } = render(<App />);
  const linkElement = getByText(/Unimplemented rules/i);
  expect(linkElement).toBeInTheDocument();
  const searchLinkElement = getByText(/Search in unimplemented/i);
  expect(searchLinkElement).toBeInTheDocument();
});
