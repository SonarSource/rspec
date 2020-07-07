import React, { useState } from "react";
import { useLocation, useHistory } from "react-router-dom";


export function useLocationSearch() {
  const location = useLocation();
  const history = useHistory();

  function setLocationSearch(searchParams, push=true) {
    const search = new URLSearchParams(location.search);

    for (const [key, value] of Object.entries(searchParams)) {
      search.set(key, value);
    }
    
    if (push) {
      history.push(`${location.pathname}?${search.toString()}`);
    } else {
      history.replace(`${location.pathname}?${search.toString()}`);
    }
  }

  return [new URLSearchParams(location.search), setLocationSearch];
}

export function useLocationSearchState(name, defaultValue, paramToState=value=>value ? value: defaultValue, stateToParam=value=>value ? value.toString(): defaultValue) {
  const [state, setState] = useState(defaultValue);
  const location = useLocation();
  const history = useHistory();

  React.useEffect(() => {
    const search = new URLSearchParams(location.search);
    if (search.has(name) && search.get(name) !== stateToParam(state)) {
      setState(paramToState(search.get(name)));
    } else if (!search.has(name) && stateToParam(state) !== stateToParam(defaultValue)) {
      setState(defaultValue);
    }
  }, [name, defaultValue, paramToState, stateToParam, state, location, history]);

  function setSearchParam(value, {push=true, skipURI=false} = {}) {
    const search = new URLSearchParams(location.search);

    search.set(name, value);
    setState(value);
    if (push) {
      history.push(`${location.pathname}?${search.toString()}`);
    } else {
      history.replace(`${location.pathname}?${search.toString()}`);
    }
  }

  return [state, setSearchParam];
}