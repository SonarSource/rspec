
import { makeStyles } from '@material-ui/core/styles';

export default makeStyles((theme) => ({
  root: {
    // marginTop: theme.spacing(1),
  },
  searchHitBox: {
    marginBottom: theme.spacing(1),
  },
  searchBar: {
    // backgroundColor: 'white'
    borderBottom: '1px solid lightgrey',
    paddingBottom: theme.spacing(2),
  },
  searchResults: {
    marginTop: theme.spacing(3),
  },
  resultsCount: {
    marginBottom: theme.spacing(2),
  }
}));
