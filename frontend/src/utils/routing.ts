import React, { useState } from "react";
import { useLocation, useHistory } from "react-router-dom";


export function useLocationSearch() {
  const location = useLocation();
  const history = useHistory();

  function setLocationSearch(searchParams: Record<string, string>, push=true) {
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

  return {searchParams: new URLSearchParams(location.search), setLocationSearch};
}

interface Serializable {
  toString: () => string
}

export type SearchParamSetter<ValueType> = (value: ValueType, { push, skipURI }?: {
  push?: boolean | undefined;
  skipURI?: boolean | undefined;
}) => void;

export function useLocationSearchState<ValueType extends Serializable = string>(
    name: string,
    defaultValue: ValueType,
    // Default paramToState function works if ValueType is string.
    paramToState=(param: any) => param !== undefined ? param: defaultValue,
    stateToParam=(state: ValueType) => state !== undefined ? state.toString(): defaultValue.toString()
  ): [ValueType, SearchParamSetter<ValueType>] {
  const [state, setState] = useState<ValueType>(defaultValue);
  const location = useLocation();
  const history = useHistory();

  React.useEffect(() => {
    const search = new URLSearchParams(location.search);
    if (search.has(name) && search.get(name) !== stateToParam(state)) {
      setState(paramToState(search.get(name)));
    } else if (!search.has(name) && stateToParam(state) !== stateToParam(defaultValue)) {
      setState(paramToState(defaultValue));
    }
  }, [name, defaultValue, paramToState, stateToParam, state, location, history]);

  function setSearchParam(value: ValueType, {push=true, skipURI=false} = {}) {
    const search = new URLSearchParams(location.search);

    search.set(name, stateToParam(value));
    setState(value);
    if (push) {
      history.push(`${location.pathname}?${search.toString()}`);
    } else {
      history.replace(`${location.pathname}?${search.toString()}`);
    }
  }

  return [state, setSearchParam];
}