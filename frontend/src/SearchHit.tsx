import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Chip from '@material-ui/core/Chip';

import { Link as RouterLink } from 'react-router-dom';
import { Link } from '@material-ui/core';
import { IndexedRule } from './types/IndexStore';
import { useRuleCoverage } from './utils/useRuleCoverage';

const blue = '#4c9bd6';
const darkerBlue = '#25699d';
const orange = '#fd6a00';
const darkerOrange = '#c45200';

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
  coveredLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: blue,
    '&:hover, &:focus': {
      backgroundColor: darkerBlue
    },
  },
  targetedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: orange,
    '&:hover, &:focus': {
      backgroundColor: darkerOrange
    },
  },
  targetedMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: orange,
    color: orange
  },
  coveredMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: blue,
    color: blue
  }
}));

type SearchHitProps = {
  data: IndexedRule
}

export function SearchHit(props: SearchHitProps) {
  const { isLanguageCovered } = useRuleCoverage();
  const classes = useStyles();

  const coveredLanguages: JSX.Element[] = [];
  const targetedLanguages: JSX.Element[] = [];

  const actualLanguages = props.data.languages.filter(language => language !== 'default');
  actualLanguages.forEach(lang => {
    const covered = isLanguageCovered(lang, props.data.all_keys);
    const chip = <Link component={RouterLink} to={`/${props.data.id}/${lang}`} style={{ textDecoration: 'none' }}>
      <Chip
        classes={{root: covered ? classes.coveredLanguageChip : classes.targetedLanguageChip }}
        label={lang}
        color="primary"
        clickable
      />
    </Link>;
    (covered ? coveredLanguages : targetedLanguages).push(chip);
  });
  const titles = props.data.titles.map(title => (
    <Typography variant="body1" component="p" gutterBottom>
      {title}
    </Typography>
  ));

  const coveredBlock = coveredLanguages.length === 0 ? <></> 
    : <Typography variant="body2" component="p" classes={{root: classes.language}}>
      <Chip classes={{root: classes.coveredMarker}} label="Covered" color="primary" variant="outlined" />
      {coveredLanguages}
    </Typography>;

  const targetedBlock = targetedLanguages.length === 0 ? <></> 
    :<Typography variant="body2" component="p" classes={{root: classes.language}}>
      <Chip classes={{root: classes.targetedMarker}} label="Targeted" color="secondary" variant="outlined" />
      {targetedLanguages}
    </Typography>;

  return (
    <Card variant="outlined" classes={{root: classes.searchHit}}>
      <CardContent>
        <Typography classes={{root: classes.ruleid}} variant="h5" component="h5" gutterBottom>
          <Link component={RouterLink} to={`/${props.data.id}`}>
            <div> Rule {props.data.id} </div>
          </Link>
        </Typography>
        {titles}
        {coveredBlock}
        {targetedBlock}
      </CardContent>
    </Card>
  )
}
