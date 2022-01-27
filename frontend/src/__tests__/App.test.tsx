import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

beforeEach(() => {
    window.history.pushState({}, 'RSPEC Search Page', '/rspec/#/rspec/');
});

test('renders see the GH PR link', () => {
  const { getByText } = render(<App />);
  const linkElement = getByText(/Rules under specification/i);
  expect(linkElement).toBeInTheDocument();
});
