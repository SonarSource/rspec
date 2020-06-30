import React from 'react';
import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import Paper from '@material-ui/core/Paper';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import { useFetch } from './utils/useFetch';
import { useHistory } from "react-router-dom";

import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
  description: {
    textAlign: 'justify'
  },
  languageBar: {
    ruleid: {
      textAlign: 'left',
    },
    flexGrow: 1,
  },
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

  let [descHTML, descError, descIsLoading] = useFetch(descUrl, null, false);
  let [metadataJSON, metadataError, metadataIsLoading] = useFetch(metadataUrl, null, true);

  let title = "Loading..."
  let languagesTabs = null;
  if (!metadataIsLoading && !metadataError) {
    title = metadataJSON.title
    metadataJSON.all_languages.sort()
    languagesTabs = metadataJSON.all_languages.map(lang => <Tab label={lang} value={lang}/>)
  }

  let description = <div>Loading...</div>;
  if (!descIsLoading && !descError) {
    description = <div dangerouslySetInnerHTML={{__html: descHTML}}/>;
  }


  return (
    <div>
    <Paper className={classes.languagesBar}>
    <Typography variant="h4" className={classes.languagesBar_ruleid}>{ruleid}</Typography>
      <Tabs
          value={language}
          onChange={handleLanguageChange}
          indicatorColor="primary"
          textColor="primary"
          centered
      >
        {languagesTabs}
      </Tabs>
  </Paper>
  
    <Container maxWidth="md">
      <Typography variant="h3">{title}</Typography>
      <Typography className={classes.description}>
        {description}
      </Typography>
    </Container>
    </div>
  );
}