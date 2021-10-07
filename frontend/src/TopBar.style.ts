import { makeStyles } from '@material-ui/core/styles';

export default makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    marginBottom: '13px', // Quickfix. For some reason the topbar overlaps on the content.
    backgroundColor: '#c72b28',
  },
  homeButton: {
    marginRight: theme.spacing(2),
  },
  title: {
    flexGrow: 1,
  },
  unimplemented: {
    color: '#FFFFFF',
  },
}));
