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
import { RuleMetadata } from './types';


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
    flexGrow: 0
  },
  unimplemented: {
    color: 'red'
  }
}));

const languageToJiraProject = new Map(Object.entries({
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
  "KOTLIN": "SONARKT",
  "SCALA": "SONARSLANG",
  "GO": "SONARSLANG",
  "SECRETS": "SECRETS",
  "SWIFT": "SONARSWIFT",
  "TSQL": "SONARTSQL",
  "VB6": "SONARVBSIX",
  "XML": "SONARXML",
  "CLOUDFORMATION": "SONARIAC",
  "TERRAFORM": "SONARIAC",
}));

const languageToGithubProject = new Map(Object.entries({
  "ABAP": "sonar-abap",
  "CSHARP": "sonar-dotnet",
  "VBNET": "sonar-dotnet",
  "JAVASCRIPT": "SonarJS",
  "TYPESCRIPT": "SonarJS",
  "SWIFT": "sonar-swift",
  "KOTLIN": "sonar-kotlin",
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
  "FLEX": "sonar-flex",
  "PHP": "sonar-php",
  "PLSQL": "sonar-plsql",
  "PYTHON": "sonar-python",
  "RPG": "sonar-rpg",
  "TSQL": "sonar-tsql",
  "XML": "sonar-xml",
  "CLOUDFORMATION": "sonar-iac",
  "TERRAFORM": "sonar-iac",
  "SECRETS": "sonar-secrets",
}));

function ticketsAndImplementationPRsLinks(ruleNumber: string, title: string, language?: string) {
  if (language) {
    const upperCaseLanguage = language.toUpperCase();
    const jiraProject = languageToJiraProject.get(upperCaseLanguage);
    const githubProject = languageToGithubProject.get(upperCaseLanguage);

    const implementationPRsLink = (
      <Link href={`https://github.com/SonarSource/${githubProject}/pulls?q=is%3Apr+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
        Implementation Pull Requests
      </Link>
    );

    if (jiraProject !== undefined) {
      const ticketsLink = (
        <Link href={`https://jira.sonarsource.com/issues/?jql=project%20%3D%20${jiraProject}%20AND%20(text%20~%20%22S${ruleNumber}%22%20OR%20text%20~%20%22RSPEC-${ruleNumber}%22%20OR%20text%20~%20"${title}")`}>
          Implementation tickets on Jira
        </Link>
      );
      return {ticketsLink, implementationPRsLink};
    } else {
      const ticketsLink = (
        <Link href={`https://github.com/SonarSource/${githubProject}/issues?q=is%3Aissue+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
          Implementation issues on GitHub
        </Link>
      );
      return {ticketsLink, implementationPRsLink};
    }
  } else {
    const ticketsLink = (<div>Select a language to see the implementation tickets</div>);
    const implementationPRsLink = (<div>Select a language to see the implementation pull requests</div>);
    return {ticketsLink, implementationPRsLink};
  }
}

export function RulePage(props: any) {
  const ruleid = props.match.params.ruleid;
  // language can be absent
  const language = props.match.params.language;
  let metaDescription = "Rules Repository Search Page";
  document.title = ruleid;
  document.getElementsByName("metaTitle").forEach(element => {
    element.setAttribute("content", ruleid);
  });

  document.getElementsByName("twitter:title").forEach(element => {
    element.setAttribute("content", ruleid);
  });

  document.getElementsByName("metaUrl").forEach(element => {
    element.setAttribute("content", window.location.href);
  });

  const history = useHistory();
  function handleLanguageChange(event: any, lang: string) {
    history.push(`/${ruleid}/${lang}`);
  }

  const classes = useStyles();
  let branch = 'master'

  let descUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + (language ?? "default") + "-description.html";
  let metadataUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + (language ?? "default") + "-metadata.json";

  let [descHTML, descError, descIsLoading] = useFetch<string>(descUrl, false);
  let [metadataJSON, metadataError, metadataIsLoading] = useFetch<RuleMetadata>(metadataUrl);

  const {ruleCoverage, allLangsRuleCoverage} = useRuleCoverage();
  let coverage: any = "Loading...";

  let title = "Loading..."
  let metadataJSONString;
  let languagesTabs = null;
  let prUrl: string | undefined = undefined;
  if (metadataJSON && !metadataIsLoading && !metadataError) {
    title = metadataJSON.title;
    metaDescription = title;
    if ('prUrl' in metadataJSON) {
      prUrl = metadataJSON.prUrl;
    }
    branch = metadataJSON.branch;
    metadataJSON.all_languages.sort();
    languagesTabs = metadataJSON.all_languages.map(lang => <Tab label={lang} value={lang}/>);
    metadataJSONString = JSON.stringify(metadataJSON, null, 2);

    const coverageMapper = (key: any, version: any) => {
      return (
        <li>{key}: {version}</li>
      )
    };
    if (language) {
      coverage = ruleCoverage(language, metadataJSON.allKeys, coverageMapper);
    } else {
      coverage = allLangsRuleCoverage(metadataJSON.allKeys, coverageMapper);
    }
  }

  document.getElementsByName("metaDescription").forEach(element => {
    element.setAttribute("content", metaDescription);
  });

  document.getElementsByName("twitter:description").forEach(element => {
    element.setAttribute("content", metaDescription);
  });

  let editOnGithubUrl = 'https://github.com/SonarSource/rspec/blob/' +
                        branch + '/rules/' + ruleid + (language ? '/' + language : '');

  let description = <div>Loading...</div>;
  if (descHTML !== null && !descIsLoading && !descError) {
    description = <div>
      <div dangerouslySetInnerHTML={{__html: descHTML}}/>
      <hr />
      <a href={editOnGithubUrl}>Edit on Github</a><br/>
      <hr />
      <pre>{metadataJSONString}</pre>
    </div>;
  }
  let prLink = <></>;
  if (prUrl) {
      prLink = <div><span className={classes.unimplemented}>Not implemented (see <a href={prUrl}>PR</a>)</span></div>
  }
  const ruleNumber = ruleid.substring(1);

  const specificationPRsLink = (
    <Link href={`https://github.com/SonarSource/rspec/pulls?q=is%3Apr+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
      Specification Pull Requests
    </Link>
  );

  const {ticketsLink, implementationPRsLink} = ticketsAndImplementationPRsLinks(ruleNumber, title, language);
  const tabsValue = language ? {'value' : language} : {'value': false};

  return (
    <div>
    <div className={classes.ruleBar}>
      <Container>
      <Typography variant="h2" classes={{root: classes.ruleid}}>{ruleid}</Typography>
      <Typography variant="h4" classes={{root: classes.ruleid}}>{prLink}</Typography>
      <Tabs
          {...tabsValue}
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
      <Box className={classes.coverage}>
        <Typography variant="h4" >Covered Since</Typography>
        <ul>
        {coverage}
        </ul>
      </Box>

      <Box className={classes.coverage}>
        <Typography variant="h4" >Related Tickets and Pull Requests</Typography>
        <ul>
          {specificationPRsLink}
        </ul>
        <ul>
          {implementationPRsLink}
        </ul>
        <ul>
          {ticketsLink}
        </ul>
      </Box>

      <Box>
        <Typography variant="h4">Description</Typography>
        <Typography className={classes.description}>
          {description}
        </Typography>
      </Box>
    </Container>
    </div>

  );
}
