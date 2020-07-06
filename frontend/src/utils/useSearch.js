import React, { useState } from 'react';

import * as lunr from 'lunr'

import { useFetch } from './useFetch';

export function useSearch(query, pageSize, pageNumber) {
  let indexDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index.json`;
  let storeDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-store.json`;

  const [indexData, indexDataError, indexDataIsLoading] = useFetch(indexDataUrl);
  const [storeData, storeDataError, storeDataIsLoading] = useFetch(storeDataUrl);
  const [index, setIndex] = useState(null);

  const [results, setResults] = useState([]);
  const [numberOfHits, setNumberOfHits] = useState(null);
  const [error, setError] = useState(null);
  const [resultsAreloading, setResultsAreLoading] = useState(true);

  React.useEffect(() => {
    console.log(`trying to load index`);
    if (!indexDataIsLoading && !indexDataError) {
      console.log("Loading Index");
      setIndex(lunr.Index.load(indexData));
    }
  }, [indexData, indexDataError, indexDataIsLoading]);

  React.useEffect(() => {
    console.log(`trying to run query`);
    if (index != null && !storeDataIsLoading && !storeDataError) {
      console.log("run Query");
      let finalQuery = "";
      if (query) {
        finalQuery = `${query}`
      }

      let hits = []
      setError(null);
      try {
        hits = index.search(finalQuery);
      } catch (exception) {
        if (exception instanceof lunr.QueryParseError) {
          setError(exception.message);
        } else {
          throw exception;
        }
      }
      setNumberOfHits(hits.length)
      // const pageResults = hits;
      const pageResults = hits.slice(pageSize*(pageNumber - 1), pageSize*(pageNumber));
      setResults(pageResults.map(({ ref }) => storeData[ref]));
      setResultsAreLoading(false);
    }
  }, [query, pageSize, pageNumber, storeData, storeDataIsLoading, storeDataError, index]);

  return [results, numberOfHits, error, resultsAreloading];
}