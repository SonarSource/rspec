import React from 'react';
import CssBaseline from '@material-ui/core/CssBaseline';
import { Box } from '@material-ui/core';
import useStyles from './App.style';
import {
  HashRouter as Router,
  Switch,
  Route
} from "react-router-dom";
import {RulePage} from "./RulePage";
import {SearchPage} from "./SearchPage";
import TopBar from "./TopBar";


function App() {
  const classes = useStyles();
  return (
    <CssBaseline>
    <div className={classes.root}>
      <TopBar/>
      <Box>
        <Router basename="/rspec">
          <Switch>
            <Route path="/:ruleid/:language" component={RulePage} />
            <Route>
              <SearchPage/>
            </Route>
          </Switch>
        </Router>
      </Box>
    </div>
    </CssBaseline>
  );
}

export default App;
