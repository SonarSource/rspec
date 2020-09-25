import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Box from '@material-ui/core/Box';
import { Link } from '@material-ui/core';

import { useHistory } from "react-router-dom";

import { useRuleCoverage } from './utils/useRuleCoverage';
import { useFetch } from './utils/useFetch';


const useStyles = makeStyles((theme) => ({
  ruleBar: {
    borderBottom: '1px solid lightgrey',
  },
  ruleid: {
    textAlign: 'center',
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(3),
  },
  title: {
    textAlign: 'justify',
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  coverage: {
    marginBottom: theme.spacing(3),
  },
  description: {
    textAlign: 'justify',
    // marginBottom: theme.spacing(3),
  },

  // style used to center the tabs when there too few of them to fill the container
  tabRoot: {
    justifyContent: "center"
  },
  tabScroller: {
    flexGrow: "0"
  }
}));

const languageToJiraProject = {
  "PYTHON": "SONARPY",
  "ABAP": "SONARABAP",
  "CFAMILY": "CPP",
  "JAVA": "SONARJAVA",
  "COBOL": "SONARCOBOL",
  "FLEX": "SONARFLEX",
  "HTML": "SONARHTML",
  "PHP": "SONARPHP",
  "PLI": "SONARPLI",
  "PLSQL": "SONARPLSQL",
  "RPG": "SONARRPG",
  "APEX": "SONARSLANG",
  "RUBY": "SONARSLANG",
  "KOTLIN": "SONARSLANG",
  "SCALA": "SONARSLANG",
  "GO": "SONARSLANG",
  "SWIFT": "SONARSWIFT",
  "TSQL": "SONARTSQL",
  "VB6": "SONARVBSIX",
  "XML": "SONARXML",
};

const languageToGithubProject = {
  "ABAP": "sonar-abap",
  "CSHARP": "sonar-dotnet",
  "VBNET": "sonar-dotnet",
  "JAVASCRIPT": "SonarJS",
  "TYPESCRIPT": "SonarJS",
  "SWIFT": "sonar-swift",
  "KOTLIN": "slang-enterprise",
  "GO": "slang-enterprise",
  "SCALA": "slang-enterprise",
  "RUBY": "slang-enterprise",
  "APEX": "slang-enterprise",
  "HTML": "sonar-html",
  "COBOL": "sonar-cobol",
  "VB6": "sonar-vb",
  "JAVA": "sonar-java",
  "PLI": "sonar-pli",
  "CFAMILY": "sonar-cpp",
  "CSS": "sonar-css",
  "PHP": "sonar-php",
  "PL/SQL": "sonar-plsql",
  "Python": "sonar-python",
  "RPG": "sonar-rpg",
  "Swift": "sonar-swift",
  "T-SQL": "sonar-tsql",
  "XML": "sonar-xml",
}


export function RulePage(props) {
  const ruleid = props.match.params.ruleid;
  const language = props.match.params.language;

  const history = useHistory();
  function handleLanguageChange(event, lang) {
    history.push(`/${ruleid}/${lang}`);
  }

  const classes = useStyles();

  let descUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + language + "-description.html";
  let metadataUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + language + "-metadata.json";
  let editOnGithubUrl = 'https://github.com/SonarSource/rspec/tree/master/rules/' + ruleid + '/' + language;

  let [descHTML, descError, descIsLoading] = useFetch(descUrl, null, false);
  let [metadataJSON, metadataError, metadataIsLoading] = useFetch(metadataUrl, null, true);

  const ruleCoverage = useRuleCoverage();
  let coverage = "Loading...";

  let title = "Loading..."
  let metadataJSONString;
  let languagesTabs = null;
  if (!metadataIsLoading && !metadataError) {
    title = metadataJSON.title
    metadataJSON.all_languages.sort()
    languagesTabs = metadataJSON.all_languages.map(lang => <Tab label={lang} value={lang}/>)
    metadataJSONString = JSON.stringify(metadataJSON, null, 2);

    coverage = ruleCoverage(language, metadataJSON.allKeys, (key, version) => {
      return (
      <li>{key}: {version}</li>
      )
    });
  }

  let description = <div>Loading...</div>;
  if (!descIsLoading && !descError) {
    description = <div>
      <div dangerouslySetInnerHTML={{__html: descHTML}}/>
      <hr />
      <a href={editOnGithubUrl}>Edit on Github</a><br/>
      <hr />
      <pre>{metadataJSONString}</pre>
    </div>;
  }
  const ruleNumber = ruleid.substring(1)
  
  const upperCaseLanguage = language.toUpperCase();
  const jiraProject = languageToJiraProject[upperCaseLanguage];
  const githubProject = languageToGithubProject[upperCaseLanguage];

  let ticketsLink;
  if (upperCaseLanguage in languageToJiraProject) {
    ticketsLink = (
        <Link href={`https://jira.sonarsource.com/issues/?jql=project%20%3D%20${jiraProject}%20AND%20(text%20~%20%22S${ruleNumber}%22%20OR%20text%20~%20%22RSPEC-${ruleNumber}%22%20OR%20text%20~%20"${title}")`}>
          Jira Tickets
        </Link>
      );
  } else {
    ticketsLink = (
      <Link href={`https://github.com/SonarSource/${githubProject}/issues?q=is%3Aissue+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
        Github Tickets
      </Link>
    );
  }
  
  const pullRequestsLink = (
    <Link href={`https://github.com/SonarSource/${githubProject}/pulls?q=is%3Apr+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
      Github Pull Requests
    </Link>
  );

  return (
    <div>
    <div className={classes.ruleBar}>
      <Container>
      <Typography variant="h2" classes={{root: classes.ruleid}}>{ruleid}</Typography>
      <Tabs
          value={language}
          onChange={handleLanguageChange}
          indicatorColor="primary"
          textColor="primary"
          centered
          variant="scrollable"
          scrollButtons="auto"
          classes={{ root: classes.tabRoot, scroller: classes.tabScroller }}
      >
        {languagesTabs}
      </Tabs>
      </Container>
    </div>
  
    <Container maxWidth="md">
      <Typography variant="h3" classes={{root: classes.title}}>{title}</Typography>
      <Box classes={{root: classes.coverage}}>
        <Typography variant="h4" >Covered Since</Typography>
        <ul>
        {coverage}
        </ul>
      </Box>

      <Box classes={{root: classes.coverage}}>
        <Typography variant="h4" >Related Tickets and Pull Requests</Typography>
        <ul>
          {ticketsLink}
        </ul>
        <ul>
          {pullRequestsLink}
        </ul>
      </Box>
      
      <Box classes={{root: classes.description}}>
        <Typography variant="h4">Description</Typography>
        <Typography className={classes.description}>
          {description}
        </Typography>
      </Box>
    </Container>
    </div>
    
  );
}
