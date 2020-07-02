import React, { useState } from 'react';

import * as lunr from 'lunr'

import { useFetch } from './useFetch';

export function useSearch(query) {
  let indexDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index.json`;
  let storeDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-store.json`;

  const [indexData, indexDataError, indexDataIsLoading] = useFetch(indexDataUrl);
  const [storeData, storeDataError, storeDataIsLoading] = useFetch(storeDataUrl);

  const [results, setResults] = useState([]);
  const [resultsAreloading, setResultsAreLoading] = useState(true);

  React.useEffect(() => {
    console.log(`trying to load index`);
    if (!indexDataIsLoading && !indexDataError && !storeDataIsLoading && !storeDataError) {
      console.log("Loading Index");
      const index = lunr.Index.load(indexData);
      let finalQuery = "";
      if (query) {
        finalQuery = `titles:${query}`
      }
      const hits = index.search(finalQuery);
      setResults(hits.map(({ ref }) => storeData[ref]));
      setResultsAreLoading(false);
    }
  }, [query, indexData, storeData, indexDataError, storeDataError, indexDataIsLoading, storeDataIsLoading]);

  return [results, resultsAreloading];
}