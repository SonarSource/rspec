import React, { useState } from 'react';

import * as lunr from 'lunr'

import { useFetch } from './useFetch';
import { IndexedRule, IndexStore } from '../types/IndexStore';

export function useSearch(query: string, ruleType: string|null, ruleTags: string[], pageSize: number, pageNumber: number) {
  let indexDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index.json`;
  let storeDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-store.json`;

  const [indexData, indexDataError, indexDataIsLoading] = useFetch<object>(indexDataUrl);
  const [storeData, storeDataError, storeDataIsLoading] = useFetch<IndexStore>(storeDataUrl);
  const [index, setIndex] = useState<lunr.Index|null>(null);

  const [results, setResults] = useState<IndexedRule[]>([]);
  const [numberOfHits, setNumberOfHits] = useState<number|null>(null);
  const [error, setError] = useState<string|null>(null);
  const [loading, setResultsAreLoading] = useState(true);

  React.useEffect(() => {
    console.log(`trying to load index`);
    if (indexData && !indexDataIsLoading && !indexDataError) {
      console.log("Loading Index");
      setIndex(lunr.Index.load(indexData));
    }
  }, [indexData, indexDataError, indexDataIsLoading]);

  React.useEffect(() => {
    console.log(`trying to run query`);
    if (index != null && !storeDataIsLoading && !storeDataError) {
      let hits: lunr.Index.Result[] = []
      setError(null);
      try {
        // We use index.query instead if index.search in order to fully
        // control how each filter is added and how the query is processed.
        hits = index.query(q => {
          // Add rule type filter
          if (ruleType) {
            q.term(ruleType.toLowerCase(), {
              fields: ['type'],
              presence: lunr.Query.presence.REQUIRED,
              usePipeline: false
            });
          }

          // Add rule tags filter
          ruleTags.forEach(ruleTag => {
            q.term(ruleTag, {
              fields: ['tags'],
              presence: lunr.Query.presence.REQUIRED,
              usePipeline: false
            });
          });

          // Search for each query token in titles and descriptions
          lunr.tokenizer(query).forEach(token => {
            q.term(token, {fields: ['titles', 'descriptions'], presence: lunr.Query.presence.REQUIRED})
          })
          
        });
      } catch (exception) {
        if (exception instanceof lunr.QueryParseError) {
          setError(exception.message);
        } else {
          throw exception;
        }
      }
      if (storeData) {
        setNumberOfHits(hits.length)
        const pageResults = hits.slice(pageSize*(pageNumber - 1), pageSize*(pageNumber));
        setResults(pageResults.map(({ ref }) => storeData[ref]));
        setResultsAreLoading(false);
      }
    }
  }, [query, ruleType, ruleTags, pageSize, pageNumber, storeData, storeDataIsLoading, storeDataError, index]);

  return {results, numberOfHits, error, loading};
}