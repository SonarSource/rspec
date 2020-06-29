import React from 'react';
import './App.css';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";
import {RulePage} from "./RulePage";
import TopBar from "./TopBar";

function App() {
  return (
    <div className="App">
      <TopBar/>
      <Router>
        <Switch>
          <Route path="/:ruleid/:language" component={RulePage} />
          <Route>
            <Link to={"/S3457/java"}>S3457</Link>
          </Route>
        </Switch>
      </Router>
    </div>
    // <div className="App">
    //   <iframe src={process.env.PUBLIC_URL + '/rules/S3457/java-description.html'}/>
    // </div>
  );
}

export default App;
