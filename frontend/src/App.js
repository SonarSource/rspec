import React from 'react';
import './App.css';
import {
  HashRouter as Router,
  Switch,
  Route
} from "react-router-dom";
import {RulePage} from "./RulePage";
import {SearchPage} from "./SearchPage";
import TopBar from "./TopBar";

function App() {
  return (
    <div className="App">

      <TopBar/>
      <Router basename="/rspec">
        <Switch>
          <Route path="/:ruleid/:language" component={RulePage} />
          <Route>
            <SearchPage/>
          </Route>
        </Switch>
      </Router>
    </div>
  );
}

export default App;
