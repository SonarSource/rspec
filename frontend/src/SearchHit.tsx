import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Chip from '@material-ui/core/Chip';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableRow from '@material-ui/core/TableRow';

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
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(0.5),
    backgroundColor: RULE_STATE['covered'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['covered'].darker
    },
  },
  targetedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(0.5),
    color: RULE_STATE['targeted'].color,
    borderColor: RULE_STATE['targeted'].color,
    '&:hover, &:focus': {
      color: RULE_STATE['targeted'].darker,
      borderColor: RULE_STATE['covered'].darker,
    },
  },
  removedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(0.5),
    backgroundColor: RULE_STATE['removed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['removed'].darker
    },
  },
  deprecatedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(0.5),
    backgroundColor: RULE_STATE['deprecated'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['deprecated'].darker
    },
  },
  closedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(0.5),
    marginBottom: theme.spacing(0.5),
    backgroundColor: RULE_STATE['closed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['closed'].darker
    },
  },
  coveredTitle: {
    borderColor: RULE_STATE['covered'].color,
    borderLeft: "3px solid",
    padding: theme.spacing(1)
  },
  coveredMarker: {
    borderColor: RULE_STATE['covered'].color,
    padding: theme.spacing(1),
    width: "100%"
  },
  targetedTitle: {
    borderColor: RULE_STATE['covered'].color,
    borderLeft: "3px double",
    padding: "8px"
  },
  targetedMarker: {
    borderColor: RULE_STATE['covered'].color,
    padding: "8px",
    width: "100%"
  },
  removedTitle: {
    borderColor: RULE_STATE['removed'].color,
    borderLeft: "3px solid",
    padding: "8px"
  },
  removedMarker: {
    borderColor: RULE_STATE['removed'].color,
    padding: "8px",
    width: "100%"
  },
  deprecatedTitle: {
    borderColor: RULE_STATE['deprecated'].color,
    borderLeft: "3px solid",
    padding: "8px"
  },
  deprecatedMarker: {
    borderColor: RULE_STATE['deprecated'].color,
    padding: "8px",
    width: "100%"
  },
  closedTitle: {
    borderColor: RULE_STATE['closed'].color,
    borderLeft: "3px solid",
    padding: "8px"
  },
  closedMarker: {
    borderColor: RULE_STATE['closed'].color,
    padding: "8px",
    width: "100%"
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

  const actualLanguages = props.data.supportedLanguages.filter(l => l.name !== 'default');
  actualLanguages.forEach(lang => {
    const ruleState = ruleStateInAnalyzer(lang.name, props.data.all_keys, lang.status);
    const chip = <Link key={lang.name} component={RouterLink} to={`/${props.data.id}/${lang.name}`}
                       style={{ textDecoration: 'none' }}>
      <Chip
        classes={{root: (classes as any)[ruleState + 'LanguageChip']}}
        label={lang.name}
        color="primary"
        variant={ruleState === 'targeted' ? 'outlined' : 'default'}
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

  const coveredRow = coveredLanguages.length === 0 ? <></>
    : <TableRow>
      <TableCell classes={{ root: classes.coveredTitle }}>Covered</TableCell>
      <TableCell classes={{ root: classes.coveredMarker }}>{coveredLanguages}</TableCell>
    </TableRow>;

  const targetedRow = targetedLanguages.length === 0 ? <></>
    : <TableRow>
      <TableCell classes={{ root: classes.targetedTitle }}>Targeted</TableCell>
      <TableCell classes={{ root: classes.targetedMarker }}>{targetedLanguages}</TableCell>
    </TableRow>;

  const deprecatedRow = deprecatedLanguages.length === 0 ? <></>
    : <TableRow>
      <TableCell classes={{ root: classes.deprecatedTitle }}>Deprecated</TableCell>
      <TableCell classes={{ root: classes.deprecatedMarker }}>{deprecatedLanguages}</TableCell>
    </TableRow>;

  const removedRow = removedLanguages.length === 0 ? <></>
    : <TableRow>
      <TableCell classes={{ root: classes.removedTitle }}>Removed</TableCell>
      <TableCell classes={{ root: classes.removedMarker }}>{removedLanguages}</TableCell>
    </TableRow>;

  const closedRow = closedLanguages.length === 0 ? <></>
    : <TableRow>
      <TableCell classes={{ root: classes.closedTitle }}>Closed</TableCell>
      <TableCell classes={{ root: classes.closedMarker }}>{closedLanguages}</TableCell>
    </TableRow>;

  return (
    <Card variant="outlined" classes={{ root: classes.searchHit }}>
      <CardContent>
        <Typography key="rule-id" classes={{ root: classes.ruleid }} variant="h5" component="h5" gutterBottom>
          <Link component={RouterLink} to={`/${props.data.id}`} data-testid={`search-hit-${props.data.id}`}>
            <div> Rule {props.data.id} </div>
          </Link>
        </Typography>
        {titles}

        <TableContainer>
          <Table >
            <TableBody>
              {coveredRow}
              {targetedRow}
              {removedRow}
              {deprecatedRow}
              {closedRow}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  )
}
