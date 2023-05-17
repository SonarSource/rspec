import React, { KeyboardEvent } from 'react';

import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import Pagination from '@material-ui/lab/Pagination';
import Box from '@material-ui/core/Box';

import useStyles from './SearchPage.style';
import { useSearch } from './utils/useSearch';
import { useFetch } from './utils/useFetch';
import {
  SearchParamSetter,
  useLocationSearch,
  useLocationSearchState
} from './utils/routing';
import { SearchHit } from './SearchHit';
import { IndexedRule, IndexAggregates } from './types/IndexStore';

import { useHistory } from 'react-router-dom';

function correctResultsOrder(results: IndexedRule[], query: string) {
  const upperCaseQuery = query.toLocaleUpperCase();
  let reorderedResults: IndexedRule[] = [];

  results.forEach(indexedRule => {
    if(indexedRule.all_keys.some(key => key === upperCaseQuery)) {
      reorderedResults = [indexedRule, ...reorderedResults];
    } else {
      reorderedResults.push(indexedRule);
    }
  });
  return reorderedResults;
}

export const SearchPage = () => {
  document.title = 'Search';

  const classes = useStyles();

  const pageSize = 20;
  const [query, setQuery] = useLocationSearchState('query', '');
    const history = useHistory();

  const [ruleType, setRuleType] = useLocationSearchState('types', 'ANY');
  const allRuleTypes: Record<string,string> = {
    'BUG': 'Bug',
    'CODE_SMELL': 'Code Smell',
    'SECURITY_HOTSPOT': 'Security Hotspot',
    'VULNERABILITY': 'Vulnerability'
  };

  const [ruleTags, setRuleTags] = useLocationSearchState<string[]>('tags', [], value => value ? value.split(',') : []);
  const [qualityProfiles, setQualityProfiles] = useLocationSearchState<string[]>('qualityProfiles', [], value => value ? value.split(',') : []);
  const [ruleLang, setLanguage] = useLocationSearchState('lang', 'ANY');

  const [pageNumber, setPageNumber] = useLocationSearchState('page', 1, parseInt);
  const {setLocationSearch} = useLocationSearch();


  const {results, numberOfHits, error, loading} = useSearch(query,
    ruleType === 'ANY' ? null : ruleType,
    ruleLang === 'ANY' ? null : ruleLang,
    ruleTags,
    qualityProfiles,
    pageSize, pageNumber);
  const totalPages = numberOfHits ? Math.ceil(numberOfHits/pageSize) : 0;

  let allRuleTags:string[] = [];
  let allLangs:string[] = [];
  let allQualityProfiles = ['Sonar way', 'Sonar way recommended'];
  const aggregatesDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-aggregates.json`;
  const [aggregatesData, aggregatesDataError, aggregatesDataIsLoading] = useFetch<IndexAggregates>(aggregatesDataUrl);

  if (aggregatesData && !aggregatesDataIsLoading && !aggregatesDataError) {
    allRuleTags = Object.keys(aggregatesData.tags).sort();
    allLangs = Object.keys(aggregatesData.langs).sort();
    allQualityProfiles = Object.keys(aggregatesData.qualityProfiles).sort();
  }

  let resultsDisplay: string|JSX.Element[] = 'No rule found...';
  if (loading) {
    resultsDisplay = 'Searching';
  } else if (results.length > 0) {
    const resultsBoxes: JSX.Element[] = [];

    // making the exact match to appear first in the search results
    correctResultsOrder(results, query).forEach(indexedRule => {
      const box = <Box key={indexedRule.id} className={classes.searchHitBox}>
        <SearchHit key={indexedRule.id} data={indexedRule}/>
      </Box>;
      resultsBoxes.push(box);
    });
    resultsDisplay = resultsBoxes;
  }

  const paramSetters: Record<string, SearchParamSetter<any>> = {
    types: setRuleType,
    tags: setRuleTags,
    qualityProfiles: setQualityProfiles,
    lang:setLanguage,
    query: setQuery
  };
  function handleUpdate(field: string) {
    return function(event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) {
      if (pageNumber > 1) {
        const uriSearch: Record<string, any> = {
          query: query, types: ruleType, tags: ruleTags, qualityProfiles: qualityProfiles, lang: ruleLang, page: 1
        };
        uriSearch[field] = event.target.value;
        setLocationSearch(uriSearch);
      } else {
        paramSetters[field](event.target.value, {push: false});
      }
    }
  }
  function handleKeyup(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      const query = (event.target as HTMLTextAreaElement).value;
      if (/^(S|RSPEC-?)?\d{3,}$/i.exec(query)) {
        if (0 < results.length) {
          history.push(correctResultsOrder(results, query)[0].id);
        }
      } else if (1 === results.length) {
        history.push(results[0].id);
      }
    }
  }

  return (
    <div className={classes.root}>
      <div className={classes.searchBar}>
        <Container maxWidth="md">
          <Grid container>
            <Grid item xs={12}>
              <TextField
                id="title-query"
                label="Rule Title and Description"
                placeholder="Search in rule titles and descriptions"
                fullWidth
                margin="normal"
                InputLabelProps={{
                  shrink: true,
                }}
                variant="outlined"
                value={query}
                onChange={handleUpdate('query')}
                onKeyUp={handleKeyup}
                error={!!error}
                helperText={error}
              />
            </Grid>
            <Grid item xs={12} container spacing={3} className={classes.fullWidth}>
              <Grid item xs={3}>
                <TextField
                  select
                  fullWidth
                  margin="normal"
                  variant="outlined"
                  size="small"
                  label="Rule type"
                  value={ruleType}
                  onChange={handleUpdate('types')}
                  data-testid="rule-type"
                >
                  <MenuItem key="Any" value="ANY">
                    Any
                  </MenuItem>
                  {Object.keys(allRuleTypes).map((ruleType) => (
                    <MenuItem key={ruleType} value={ruleType} data-testid={`rule-type-${ruleType}`}>
                      {allRuleTypes[ruleType]}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  select
                  fullWidth
                  size="small"
                  SelectProps={{
                    multiple: true,
                    renderValue: (selected: any) => {
                      return selected.join(', ');
                    }
                  }}
                  margin="normal"
                  variant="outlined"
                  label="Rule Tags"
                  value={ruleTags}
                  onChange={handleUpdate('tags')}
                  data-testid="rule-tags"
                >
                  {allRuleTags.map((ruleTag) => (
                    <MenuItem key={ruleTag} value={ruleTag} data-testid={`rule-tag-${ruleTag}`}>
                      {ruleTag}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={4}>
                <TextField
                  select
                  fullWidth
                  margin="normal"
                  size="small"
                  variant="outlined"
                  label="Language"
                  value={allLangs.length === 0 ? '' : ruleLang}
                  onChange={handleUpdate('lang')}
                  data-testid="rule-language"
                >
                  <MenuItem key="Any" value="ANY">
                    Any
                  </MenuItem>
                  {allLangs.map((lang) => (
                    <MenuItem key={lang} value={lang} data-testid={`rule-language-${lang}`}>
                      {lang}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
            </Grid>
            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                size="small"
                SelectProps={{
                  multiple: true,
                  renderValue: (selected: any) => {
                    return selected.join(', ');
                  }
                }}
                margin="normal"
                variant="outlined"
                label="Default Quality Profiles"
                value={qualityProfiles}
                onChange={handleUpdate('qualityProfiles')}
                data-testid="rule-default-quality-profile"
              >
                {allQualityProfiles.map((qualityProfile) => (
                  <MenuItem key={qualityProfile} value={qualityProfile}
                            data-testid={`rule-qual-profile-${qualityProfile}`}>
                    {qualityProfile}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        </Container>
      </div>
      <div className={classes.searchResults}>
        <Container maxWidth="md">
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Box key="total-num" className={classes.topRow}>
                <Box className={classes.resultsCount}>
                  <Typography variant="subtitle1">Number of rules found: {numberOfHits}</Typography>
                </Box>
              </Box>
              {resultsDisplay}
              <Pagination count={totalPages} page={pageNumber} siblingCount={2}
                onChange={(event, value) => setPageNumber(value)}
              />
            </Grid>
          </Grid>
        </Container>
      </div>
    </div>
  )
}
