import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Box from '@material-ui/core/Box';

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
