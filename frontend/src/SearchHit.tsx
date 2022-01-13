import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Chip from '@material-ui/core/Chip';

import { Link as RouterLink } from 'react-router-dom';
import { Link } from '@material-ui/core';
import { IndexedRule } from './types/IndexStore';
import { RULE_STATE, useRuleCoverage } from './utils/useRuleCoverage';

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
    backgroundColor: RULE_STATE['covered'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['covered'].darker
    },
  },
  targetedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: RULE_STATE['targeted'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['targeted'].darker
    },
  },
  removedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: RULE_STATE['removed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['removed'].darker
    },
  },
  deprecatedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: RULE_STATE['deprecated'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['deprecated'].darker
    },
  },
  closedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
    backgroundColor: RULE_STATE['closed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['closed'].darker
    },
  },
  targetedMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: RULE_STATE['targeted'].color,
    color: RULE_STATE['targeted'].color
  },
  coveredMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: RULE_STATE['covered'].color,
    color: RULE_STATE['covered'].color
  },
  removedMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: RULE_STATE['removed'].color,
    color: RULE_STATE['removed'].color
  },
  deprecatedMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: RULE_STATE['deprecated'].color,
    color: RULE_STATE['deprecated'].color
  },
  closedMarker: {
    marginTop: theme.spacing(2),
    marginRight: theme.spacing(2),
    borderColor: RULE_STATE['closed'].color,
    color: RULE_STATE['closed'].color
  }
}));

type SearchHitProps = {
  data: IndexedRule
}

export function SearchHit(props: SearchHitProps) {
  const { ruleStateInAnalyzer } = useRuleCoverage();
  const classes = useStyles();

  const coveredLanguages: JSX.Element[] = [];
  const targetedLanguages: JSX.Element[] = [];
  const removedLanguages: JSX.Element[] = [];
  const deprecatedLanguages: JSX.Element[] = [];
  const closedLanguages: JSX.Element[] = [];

  const actualLanguages = props.data.languages.filter(l => l.name !== 'default');
  actualLanguages.forEach(lang => {
    const ruleState = ruleStateInAnalyzer(lang.name, props.data.all_keys, lang.status);
    const chip = <Link key={lang} component={RouterLink} to={`/${props.data.id}/${lang}`}
                       style={{ textDecoration: 'none' }}>
      <Chip
        classes={{root: (classes as any)[ruleState + 'LanguageChip']}}
        label={lang.name}
        color="primary"
        clickable
        key="{lang}"
      />
    </Link>;
    switch(ruleState) {
      case 'targeted':
        targetedLanguages.push(chip);
        break;
      case 'removed':
        removedLanguages.push(chip);
        break;
      case 'deprecated':
        deprecatedLanguages.push(chip);
        break;
      case 'closed':
        closedLanguages.push(chip);
        break;
      case 'covered':
      default:
        coveredLanguages.push(chip);
        break;
      }
  });
  const titles = props.data.titles.map(title => (
    <Typography key={title} variant="body1" component="p" gutterBottom>
      {title}
    </Typography>
  ));

  const coveredBlock = coveredLanguages.length === 0 ? <></> 
    : <Typography key="covered-marker" variant="body2" component="div" classes={{root: classes.language}}>
      <Chip classes={{root: classes.coveredMarker}} label="Covered" color="primary" variant="outlined" />
      {coveredLanguages}
    </Typography>;

  const targetedBlock = targetedLanguages.length === 0 ? <></> 
    : <Typography key="targeted-marker" variant="body2" component="div" classes={{root: classes.language}}>
      <Chip classes={{root: classes.targetedMarker}} label="Targeted" color="secondary" variant="outlined" />
      {targetedLanguages}
    </Typography>;

  const removedBlock = removedLanguages.length === 0 ? <></> 
    : <Typography key="removed-marker" variant="body2" component="div" classes={{root: classes.language}}>
      <Chip classes={{root: classes.removedMarker}} label="Removed" color="secondary" variant="outlined" />
      {removedLanguages}
    </Typography>;

  const deprecatedBlock = deprecatedLanguages.length === 0 ? <></>
    : <Typography variant="body2" component="p" classes={{ root: classes.language }}>
      <Chip classes={{ root: classes.deprecatedMarker }} label="Deprecated" color="secondary" variant="outlined" />
      {deprecatedLanguages}
    </Typography>;
  const closedBlock = closedLanguages.length === 0 ? <></>
    : <Typography variant="body2" component="p" classes={{ root: classes.language }}>
      <Chip classes={{ root: classes.closedMarker }} label="Closed" color="secondary" variant="outlined" />
      {closedLanguages}
    </Typography>;

  return (
    <Card variant="outlined" classes={{root: classes.searchHit}}>
      <CardContent>
        <Typography key="rule-id" classes={{root: classes.ruleid}} variant="h5" component="h5" gutterBottom>
          <Link component={RouterLink} to={`/${props.data.id}`}>
            <div> Rule {props.data.id} </div>
          </Link>
        </Typography>
        {titles}
        {coveredBlock}
        {targetedBlock}
        {removedBlock}
        {deprecatedBlock}
        {closedBlock}
      </CardContent>
    </Card>
  )
}
