import { makeStyles } from '@material-ui/core/styles';

export default makeStyles((theme) => ({
  root: {
    textAlign: 'left',
    backgroundColor: 'white',
  },
  appBarSpacer: theme.mixins.toolbar,
}));