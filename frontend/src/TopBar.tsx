import React from 'react';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import IconButton from '@material-ui/core/IconButton';
import Button from '@material-ui/core/Button';
import HomeIcon from '@material-ui/icons/Home';

import useStyles from './TopBar.style';

export default function TopBar() {
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
              <span className={classes.unimplemented} > Unimplemented rules </span>
            </Button>
        </Toolbar>
      </AppBar>
  );
}