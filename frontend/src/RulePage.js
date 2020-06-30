import React from 'react';
import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import { useFetch } from './utils/useFetch';


import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
  description: {
    textAlign: 'justify'
  }
}));


export function RulePage(props) {
  const ruleid = props.match.params.ruleid;
  const language = props.match.params.language;

  const classes = useStyles();

  const descUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + language + "-description.html";
  const metadataUrl = process.env.PUBLIC_URL + '/rules/' + ruleid + "/" + language + "-metadata.json";

  const [descHTML, descError, descIsLoading] = useFetch(descUrl, null, false);
  const [metadataJSON, metadataError, metadataIsLoading] = useFetch(metadataUrl);

  let metadata = <Typography variant="h2" component="h3">Loading...</Typography>;
  if (!metadataIsLoading && !metadataError) {
    metadata = <Typography variant="h2" component="h3">{metadataJSON.title}</Typography>
  }

  let description = <div>Loading...</div>;
  if (!descIsLoading && !descError) {
    description = <div dangerouslySetInnerHTML={{__html: descHTML}}/>;
  }


  return (
    <Container maxWidth="md">
      {metadata}
      <Typography className={classes.description}>
        {description}
      </Typography>
    </Container>
  );
}