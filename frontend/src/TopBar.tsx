import React from 'react';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import IconButton from '@material-ui/core/IconButton';
import Button from '@material-ui/core/Button';
import HomeIcon from '@material-ui/icons/Home';

import useStyles from './TopBar.style';

export function TopBar() {
  const classes = useStyles();

  return (
      <AppBar position="static" className={classes.root}>
        <Toolbar>
          <IconButton edge="start" className={classes.homeButton} color="inherit" aria-label="menu" href="/rspec">
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" className={classes.title}>
            SonarSource Rule Specifications
          </Typography>
            <Button href="https://github.com/SonarSource/rspec/pulls?q=is%3Aopen+is%3Apr+%22Create+rule%22">
              <span className={classes.unimplemented} > Rules under specification </span>
            </Button>
        </Toolbar>
      </AppBar>
  );
}

const languageToOfficial = new Map(Object.entries({
    'cfamily': 'cpp',
}));

function extRuleId(intRuleId: string) {
    return 'RSPEC-' + intRuleId.substr(1);
}

function extLang(intLang: string) {
    const ret = languageToOfficial.get(intLang);
    if (ret) {
        return ret;
    }
    return intLang;
}

export function LangRuleTopBar(props: any) {
    const {ruleid, language} = props.match.params;
    const classes = useStyles();

    const externalRuleid = extRuleId(ruleid);
    const externalLanguage = extLang(language);

    return (
        <AppBar position="static" className={classes.root}>
            <Toolbar>
                <IconButton edge="start" className={classes.homeButton} color="inherit" aria-label="menu" href="/rspec">
                    <HomeIcon />
                </IconButton>
                <Typography variant="h6" className={classes.title}>
                    SonarSource Rule Specifications
                </Typography>
                <Button href={`https://rules.sonarsource.com/${externalLanguage}/${externalRuleid}`}>
                    <span> Official Rule Page </span>
                </Button>
                <Button href="https://github.com/SonarSource/rspec/pulls?q=is%3Aopen+is%3Apr+%22Create+rule%22">
                    <span className={classes.unimplemented} > Rules under specification </span>
                </Button>
            </Toolbar>
        </AppBar>
    );
}
