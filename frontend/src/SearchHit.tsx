import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Chip from '@material-ui/core/Chip';

import { Link as RouterLink } from 'react-router-dom';
import { Link } from '@material-ui/core';
import { IndexedRule } from './types/IndexStore';


const useStyles = makeStyles((theme) => ({
  searchHit: {

  },
  ruleid: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  language: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
  },
  languageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: '#4c9bd6'
  },
  unimplementedMarker: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: '#fd6a00'
  }
}));

type SearchHitProps = {
  data: IndexedRule
}

export function SearchHit(props: SearchHitProps) {
  const classes = useStyles();
  const actualLanguages = props.data.languages.filter(language => language !== 'default');
  const languages = actualLanguages.map(lang => (
    <Link component={RouterLink} to={`/${props.data.id}/${lang}`} style={{ textDecoration: 'none' }}>
    <Chip
      classes={{root: classes.languageChip}}
      label={lang}
      color="primary"
      clickable
    />
    </Link>
  ));
  const titles = props.data.titles.map(title => (
    <Typography variant="body1" component="p" gutterBottom>
      {title}
    </Typography>
  ));
  let unimplementedMarker = <></>;
  if (props.data.prUrl) {
    unimplementedMarker = <Chip classes={{root: classes.unimplementedMarker}} label="Not implemented" color="secondary" />
  }
  return (
    <Card variant="outlined" classes={{root: classes.searchHit}}>
      <CardContent>
        <Typography classes={{root: classes.ruleid}} variant="h5" component="h5" gutterBottom>
          <Link component={RouterLink} to={`/${props.data.id}`}>
            <div> Rule {props.data.id} </div>
          </Link>
          {unimplementedMarker}
        </Typography>
        {titles}
        <Typography variant="body2" component="p" classes={{root: classes.language}}>
          {languages}
        </Typography>
      </CardContent>
    </Card>
  )
}
