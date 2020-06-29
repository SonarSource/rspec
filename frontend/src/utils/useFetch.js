import React from 'react';

export function useFetch(url, options=null, handleResponse=(res) => res.json()) {
  const [response, setResponse] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(url, options);
        const content = await handleResponse(res);
        setResponse(content);
        setIsLoading(false)
      } catch (exception) {
        setError(exception);
      }
    };
    fetchData();
  }, [url]);

  return [ response, error, isLoading ];
}