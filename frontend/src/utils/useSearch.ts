import React, { useState } from 'react';

import lunr from 'lunr';

import { useFetch } from './useFetch';
import { IndexedRule, IndexStore } from '../types/IndexStore';

export function addFilterForTypes(q: lunr.Query, type: string) {
  q.term(type.toLowerCase(), {
    fields: ['types'],
    presence: lunr.Query.presence.REQUIRED,
    usePipeline: false,
  });
}

export function addFilterForTags(q: lunr.Query, tags: string[]) {
  tags.forEach(tag => {
    q.term(tag, {
      fields: ['tags'],
      presence: lunr.Query.presence.REQUIRED,
      usePipeline: false,
    });
  });
}

export function addFilterForLanguages(q: lunr.Query, language: string) {
  q.term(language.toLowerCase(), {
    fields: ['languages'],
    presence: lunr.Query.presence.REQUIRED,
    usePipeline: false,
  });
}

export function addFilterForQualityProfiles(q: lunr.Query, profiles: string[]) {
  profiles.forEach(profile => {
    q.term(profile.toLowerCase(), {
      fields: ['qualityProfiles'],
      presence: lunr.Query.presence.REQUIRED,
      usePipeline: false,
    });
  });
}

export function addFilterForKeysTitlesDescriptions(q: lunr.Query, query: string) {
  lunr.tokenizer(amendQuery(query)).forEach(token => {
    q.term(token, {
      fields: ['all_keys', 'titles', 'descriptions'],
      presence: lunr.Query.presence.REQUIRED
    });
  });
}

export function useSearch(query: string, ruleType: string|null, ruleLang: string|null, ruleTags: string[],
                          qualityProfiles: string[],
                          pageSize: number, pageNumber: number) {
  const indexDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index.json`;
  const storeDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-store.json`;

  const [indexData, indexDataError, indexDataIsLoading] = useFetch<object>(indexDataUrl);
  const [storeData, storeDataError, storeDataIsLoading] = useFetch<IndexStore>(storeDataUrl);
  const [index, setIndex] = useState<lunr.Index|null>(null);

  const [results, setResults] = useState<IndexedRule[]>([]);
  const [numberOfHits, setNumberOfHits] = useState<number|null>(null);
  const [error, setError] = useState<string|null>(null);
  const [loading, setResultsAreLoading] = useState(true);

  React.useEffect(() => {
    if (indexData && !indexDataIsLoading && !indexDataError) {
      setIndex(lunr.Index.load(indexData));
    }
  }, [indexData, indexDataError, indexDataIsLoading]);

  // Avoid comparing arrays in the useEffect dependency list,
  // as that would always return unequal
  const tagsStr = ruleTags.toString();
  const profilesStr = qualityProfiles.toString();

  React.useEffect(() => {
    if (index != null && !storeDataIsLoading && !storeDataError) {
      let hits: lunr.Index.Result[] = [];
      setError(null);
      try {
        // We use index.query instead if index.search in order to fully
        // control how each filter is added and how the query is processed.
        hits = index.query(q => {
          if (ruleType) {
            addFilterForTypes(q, ruleType);
          }
          if (ruleLang) {
            addFilterForLanguages(q, ruleLang);
          }
          addFilterForTags(q, ruleTags);
          addFilterForQualityProfiles(q, qualityProfiles);
          addFilterForKeysTitlesDescriptions(q, query);
        });
      } catch (exception) {
        if (exception instanceof lunr.QueryParseError) {
          setError(exception.message);
        } else {
          throw exception;
        }
      }
      if (storeData) {
        setNumberOfHits(hits.length);
        const pageResults = hits.slice(pageSize*(pageNumber - 1), pageSize*(pageNumber));
        setResults(pageResults.map(({ ref }) => storeData[ref]));
        setResultsAreLoading(false);
      }
    }
    // ruleTags and qualityProfiles are replaced with tagsStr and profilesStr
    // to enable correct equality comparison when react decides whether to
    // re invoke the effect.
    // eslint-disable-next-line
  }, [query, ruleType, ruleLang, tagsStr, profilesStr, pageSize, pageNumber,
      storeData, storeDataIsLoading, storeDataError, index]);

  return {results, numberOfHits, error, loading};
}

// allows to search by a rule key in the following formats: SXXX, RSPEC-XXX
function amendQuery(query: string) {
  return query.replace('RSPEC-', 'S');
}
