import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import MenuItem from '@material-ui/core/MenuItem';
import Container from '@material-ui/core/Container';
import Grid from '@material-ui/core/Grid';
import Pagination from '@material-ui/lab/Pagination';

import { useSearch } from './utils/useSearch';
import {
  useLocationSearch,
  useLocationSearchState
} from './utils/routing';
import { SearchHit } from './SearchHit';


const classes = makeStyles((theme) => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',
  },
  textField: {
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    width: '25ch',
  }
}));

export const SearchPage = () => {
  const pageSize = 20;
  const [query, setQuery] = useLocationSearchState('query', '');

  const [ruleType, setRuleType] = useLocationSearchState('types', 'ALL');
  const allRuleTypes = {'BUG': 'Bug', 'CODE_SMELL': 'Code Smell', 'SECURITY_HOTSPOT': 'Security Hotspot', 'VULNERABILITY': 'Vulnerability'};

  const [ruleTags, setRuleTags] = useLocationSearchState('tags', [], value => value ? value.split(',') : []);
  const allRuleTags = ["confusing", 'pitfall', 'clumsy', 'junit', 'tests']; // TODO: generate this list

  const [pageNumber, setPageNumber] = useLocationSearchState('page', 1, parseInt);
  const [, setLocationSearch] = useLocationSearch();


  const [results, numberOfHits, error, resultsAreLoading] = useSearch(query,
    ruleType === "ALL" ? null : ruleType,
    ruleTags,
    pageSize, pageNumber);
  const totalPages = Math.ceil(numberOfHits/pageSize);

  let resultsDisplay="No rule found...";
  if (resultsAreLoading) {
    resultsDisplay = "Searching";
  }
  else if (results.length > 0) {
    resultsDisplay = results.map(result => <SearchHit key={result.id} data={result}/>)
  }

  const paramSetters = {types: setRuleType, tags: setRuleTags, query: setQuery};
  function handleUpdate(field) {
    return function(event) {
      if (pageNumber > 1) {
        const uriSearch = {query: query, types: ruleType, tags: ruleTags, page: 1};
        uriSearch[field] = event.target.value;
        setLocationSearch(uriSearch);
      } else {
        paramSetters[field](event.target.value, {push: false});
      }
    }
  }

  return (
    <div>
    <Paper className={classes.languagesBar}>
    <Container maxWidth="md">
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h4" className={classes.searchBar}>Search Rule Specifications</Typography>
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
            error={error}
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
          }}
          margin="normal"
          variant="outlined"
          label="Rule Tags"
          value={ruleTags}
          onChange={handleUpdate("tags")}
          renderValue={(selected) => {
            return selected.join(', ');
          }}
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
  </Paper>
  <Container maxWidth="md" className={classes.searchHitsContainer}>
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h5" className={classes.searchBar}>Number of rules found: {numberOfHits}</Typography>
        <ul>
          {resultsDisplay}
        </ul>
        <Pagination count={totalPages} page={pageNumber} siblingCount={2}
          onChange={(event, value) => setPageNumber(value)}
          />
      </Grid>
    </Grid>
  </Container>
  </div>
  )
}