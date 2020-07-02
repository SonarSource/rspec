import React, { useState } from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';
import Container from '@material-ui/core/Container';

import { useSearch } from './utils/useSearch';
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
  const [titleQuery, setTitleQuery] = useState("");

  const [results, resultsAreLoading] =  useSearch(titleQuery);

  let resultsDisplay="No rule found...";
  if (resultsAreLoading) {
    resultsDisplay = "Searching";
  }
  else if (results.length > 0) {
    resultsDisplay = results.map(result => <SearchHit key={result.id} data={result}/>)
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
          value={titleQuery}
          onChange={e => setTitleQuery(e.target.value)}
      />
    </Container>
  </Paper>
    <h1>Results</h1>
    <ul>
      {resultsDisplay}
    </ul>
    </div>
  )
}