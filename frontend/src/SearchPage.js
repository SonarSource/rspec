import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import Container from '@material-ui/core/Container';
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
  },
}));

export const SearchPage = () => {
  const pageSize = 20;
  const [query, setQuery] = useLocationSearchState('query', '');
  const [pageNumber, setPageNumber] = useLocationSearchState('page', 1, parseInt);
  const [, setLocationSearch] = useLocationSearch();


  const [results, numberOfHits, error, resultsAreLoading] =  useSearch(query, pageSize, pageNumber);
  const totalPages = Math.ceil(numberOfHits/pageSize);

  let resultsDisplay="No rule found...";
  if (resultsAreLoading) {
    resultsDisplay = "Searching";
  }
  else if (results.length > 0) {
    resultsDisplay = results.map(result => <SearchHit key={result.id} data={result}/>)
  }

  function handleQueryUpdate(event) {
    if (pageNumber > 1) {
      setLocationSearch({query: event.target.value, page: 1});
    } else {
      setQuery(event.target.value, {push: false});
    }
  }
 
  return (
    <div>
    <Paper className={classes.languagesBar}>
    <Container maxWidth="md">
      <Typography variant="h4" className={classes.searchBar}>Search Rule Specifications</Typography>
      <TextField
          id="title-query"
          label="Rule Title"
          style={{ margin: 8 }}
          placeholder="Search for a rule title"
          fullWidth
          margin="normal"
          InputLabelProps={{
            shrink: true,
          }}
          variant="outlined"
          value={query}
          onChange={handleQueryUpdate}
          error={error}
          helperText={error}
      />
    </Container>
  </Paper>
      <Typography variant="h5" className={classes.searchBar}>Number of rules found: {numberOfHits}</Typography>
    <ul>
      {resultsDisplay}
    </ul>
    <Pagination count={totalPages} page={pageNumber} siblingCount={2}
      onChange={(event, value) => setPageNumber(value)}
      />
    <Paper/>
    </div>
  )
}