import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';

import { Link } from "react-router-dom";


const classes = makeStyles((theme) => ({
}));

export function SearchHit(props) {
  return (
    <Card className={classes.searchHit}>
      <CardContent>
        <Link to={`/S${props.data.id}/${props.data.languages[0]}`}>
          <Typography className={classes.title} variant="h5" component="h2" gutterBottom>
          {props.data.titles}
          </Typography>
          <Typography variant="body2" component="p">
            {props.data.languages[0]}
          </Typography>
        </Link>
      </CardContent>
    </Card>
  )
}