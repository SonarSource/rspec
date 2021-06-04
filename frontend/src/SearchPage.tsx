import React from 'react';

import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import Pagination from '@material-ui/lab/Pagination';
import Box from '@material-ui/core/Box';

import useStyles from './SearchPage.style';
import { useSearch } from './utils/useSearch';
import {
  SearchParamSetter,
  useLocationSearch,
  useLocationSearchState
} from './utils/routing';
import { SearchHit } from './SearchHit';

export const SearchPage = () => {
  const classes = useStyles();
  
  const pageSize = 20;
  const [query, setQuery] = useLocationSearchState('query', '');

  const [ruleType, setRuleType] = useLocationSearchState('types', 'ALL');
  const allRuleTypes: Record<string,string> = {
    'BUG': 'Bug',
    'CODE_SMELL': 'Code Smell', 
    'SECURITY_HOTSPOT': 'Security Hotspot',
    'VULNERABILITY': 'Vulnerability'
  };

  const [ruleTags, setRuleTags] = useLocationSearchState<string[]>('tags', [], value => value ? value.split(',') : []);
  const allRuleTags = ["confusing", 'pitfall', 'clumsy', 'junit', 'tests']; // TODO: generate this list

  const [pageNumber, setPageNumber] = useLocationSearchState('page', 1, parseInt);
  const {setLocationSearch} = useLocationSearch();


  const {results, numberOfHits, error, loading} = useSearch(query,
    ruleType === "ALL" ? null : ruleType,
    ruleTags,
    pageSize, pageNumber);
  const totalPages = numberOfHits ? Math.ceil(numberOfHits/pageSize) : 0;

  let resultsDisplay: string|JSX.Element[] = "No rule found...";
  if (loading) {
    resultsDisplay = "Searching";
  }
  else if (results.length > 0) {
    resultsDisplay = results.map(result =>
      <Box className={classes.searchHitBox}>
        <SearchHit key={result.id} data={result}/>
      </Box>
    )
  }

  const paramSetters: Record<string, SearchParamSetter<any>> = {types: setRuleType, tags: setRuleTags, query: setQuery};
  function handleUpdate(field: string) {
    return function(event: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) {
      if (pageNumber > 1) {
        const uriSearch: Record<string, any> = {
          query: query, types: ruleType, tags: ruleTags, page: 1
        };
        uriSearch[field] = event.target.value;
        setLocationSearch(uriSearch);
      } else {
        paramSetters[field](event.target.value, {push: false});
      }
    }
  }

  return (
    <div className={classes.root}>
    <div className={classes.searchBar}>
    <Container maxWidth="md">
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4">Search Rule Specifications</Typography>
      </Grid>
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
            onChange={handleUpdate("query")}
            error={!!error}
            helperText={error}
        />
      </Grid>
      <Grid item xs={3}>
        <TextField
          select
          fullWidth
          margin="normal"
          variant="outlined"
          label="Rule types"
          value={ruleType}
          onChange={handleUpdate("types")}
        >
          <MenuItem key="All" value="ALL">
            All
          </MenuItem>
          {Object.keys(allRuleTypes).map((ruleType) => (
            <MenuItem key={ruleType} value={ruleType}>
              {allRuleTypes[ruleType]}
            </MenuItem>
          ))}
        </TextField>
      </Grid>
      <Grid item xs={9}>
      <TextField
          select
          fullWidth
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
          onChange={handleUpdate("tags")}
        >
          {allRuleTags.map((ruleType) => (
            <MenuItem key={ruleType} value={ruleType}>
              {ruleType}
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
          <Box className={classes.topRow}>
            <Box className={classes.resultsCount}>
              <Typography variant="subtitle1">Number of rules found: {numberOfHits}</Typography>
            </Box>
            <Typography variant="subtitle1">
              <a href={"https://github.com/SonarSource/rspec/pulls?q=is%3Aopen+is%3Apr+%22Create+rule%22+" + query}>Search in unimplemented</a>
            </Typography>
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