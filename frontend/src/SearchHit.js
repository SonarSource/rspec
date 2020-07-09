import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Chip from '@material-ui/core/Chip';

import { Link as RouterLink } from 'react-router-dom';
import { Link } from '@material-ui/core';


const useStyles = makeStyles((theme) => ({
  searchHit: {

  },
  ruleid: {
  },
  // languages: {
  // },
  language: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
  }
}));

export function SearchHit(props) {
  const classes = useStyles();
  const languages = props.data.languages.map(lang => (
    <Chip
      classes={{root: classes.language}}
      label={lang}
      color="primary"
    />
  ));
  const titles = props.data.titles.split('\n').map(title => (
    <Typography className={{root: classes.title}} variant="body1" component="p" gutterBottom>
      {title}
    </Typography>
  ));
  return (
    <Link component={RouterLink} to={`/S${props.data.id}/${props.data.languages[0]}`}>
    <Card variant="outlined" classes={{root: classes.searchHit}}>
      <CardContent>
          <Typography classes={{root: classes.ruleid}} variant="h5" component="h5" gutterBottom>
            Rule {props.data.id}
          </Typography>
          {titles}
          <Typography variant="body2" component="p" classes={{root: classes.languages}}>
            {languages}
          </Typography>
      </CardContent>
    </Card>
    </Link>
  )
}