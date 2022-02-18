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

const CHIP_V_MARGIN = 0.5;
const TABLE_PADDING = 1;

const useStyles = makeStyles((theme) => ({
  searchHit: {

  },
  ruleid: {
    display: 'flex',
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  avoid: {
    textDecoration: 'line-through'
  },
  language: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(2),
  },
  coveredLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(CHIP_V_MARGIN),
    marginBottom: theme.spacing(CHIP_V_MARGIN),
    backgroundColor: RULE_STATE['covered'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['covered'].darker
    },
  },
  targetedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(CHIP_V_MARGIN),
    marginBottom: theme.spacing(CHIP_V_MARGIN),
    color: RULE_STATE['targeted'].color,
    borderColor: RULE_STATE['targeted'].color,
    '&:hover, &:focus': {
      color: RULE_STATE['targeted'].darker,
      borderColor: RULE_STATE['covered'].darker,
    },
  },
  removedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(CHIP_V_MARGIN),
    marginBottom: theme.spacing(CHIP_V_MARGIN),
    backgroundColor: RULE_STATE['removed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['removed'].darker
    },
  },
  deprecatedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(CHIP_V_MARGIN),
    marginBottom: theme.spacing(CHIP_V_MARGIN),
    backgroundColor: RULE_STATE['deprecated'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['deprecated'].darker
    },
  },
  closedLanguageChip: {
    marginRight: theme.spacing(1),
    marginTop: theme.spacing(CHIP_V_MARGIN),
    marginBottom: theme.spacing(CHIP_V_MARGIN),
    backgroundColor: RULE_STATE['closed'].color,
    '&:hover, &:focus': {
      backgroundColor: RULE_STATE['closed'].darker
    },
  },
  coveredTitle: {
    borderColor: RULE_STATE['covered'].color,
    padding: theme.spacing(TABLE_PADDING)
  },
  coveredMarker: {
    padding: theme.spacing(TABLE_PADDING),
    width: '100%'
  },
  targetedTitle: {
    borderColor: RULE_STATE['covered'].color,
    padding: theme.spacing(TABLE_PADDING)
  },
  targetedMarker: {
    padding: theme.spacing(TABLE_PADDING),
    width: '100%'
  },
  removedTitle: {
    borderColor: RULE_STATE['removed'].color,
    padding: theme.spacing(TABLE_PADDING)
  },
  removedMarker: {
    padding: theme.spacing(TABLE_PADDING),
    width: '100%'
  },
  deprecatedTitle: {
    borderColor: RULE_STATE['deprecated'].color,
    padding: theme.spacing(TABLE_PADDING)
    },
  deprecatedMarker: {
    padding: theme.spacing(TABLE_PADDING),
    width: '100%'
  },
  closedTitle: {
    borderColor: RULE_STATE['closed'].color,
    padding: theme.spacing(TABLE_PADDING)
  },
  closedMarker: {
    padding: theme.spacing(TABLE_PADDING),
    width: '100%'
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
  const ruleStates = actualLanguages.map(l => ({
    lang: l.name,
    ruleState: ruleStateInAnalyzer(l.name, props.data.all_keys, l.status)
  }));

  ruleStates.forEach(({lang, ruleState}) => {
    const chip = <Link key={lang} component={RouterLink} to={`/${props.data.id}/${lang}`}
                       style={{ textDecoration: 'none' }}>
      <Chip
        classes={{root: (classes as any)[ruleState + 'LanguageChip']}}
        label={lang}
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
  const avoid = !ruleStates.some(({ ruleState }) => ruleState === 'targeted' || ruleState === 'covered');
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
        <Typography key="rule-id" classes={{ root: `${classes.ruleid} ${avoid ? classes.avoid : ''}` }}
                    variant="h5" component="h5" gutterBottom>
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
