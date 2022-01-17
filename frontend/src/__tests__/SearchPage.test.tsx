import React from 'react';
import path from 'path';
import { render } from '@testing-library/react';
import { SearchPage } from '../SearchPage';
import { buildIndexStore, buildSearchIndex } from '../deployment/searchIndex';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { fetchMock } from '../testutils';

function normalize(obj) {
    // Lunr (the search engine) expects its objects to have been
    // serialized and deserialized when it is queried.
    // This is not a no-op, because, for example, it translates function references to
    // simple labels on the serialization step, and then uses these labels to
    // restore the function references when loading.
    return JSON.parse(JSON.stringify(obj));
}

beforeEach(() => {
    const rulePath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'metadata');
    const [indexStore, indexAggregates] = buildIndexStore(rulePath);
    const searchIndex = buildSearchIndex(indexStore);
    const rootUrl = process.env.PUBLIC_URL;
    let mockUrls = {};
    mockUrls[`${rootUrl}/rules/rule-index.json`] = {json: normalize(searchIndex)};
    mockUrls[`${rootUrl}/rules/rule-index-store.json`] = {json: normalize(indexStore)};
    mockUrls[`${rootUrl}/rules/rule-index-aggregates.json`] = {json: normalize(indexAggregates)};
    mockUrls[`${rootUrl}/covered_rules.json`] = {json:
        {'CPP': {'S1000': 'ver1', 'S987': 'ver2', 'S3457': 'ver1'},
         'C': {'S1000': 'c1', 'S234': {'since': 'c2', 'until': 'c3'}},
         'PY': {'S3457': {'since': 'p2', 'until': 'p3'}}}
    };
    jest.spyOn(global, 'fetch').mockImplementation(fetchMock(mockUrls));
});

afterEach(() => {
    global.fetch.mockClear();
});

test('renders the list of all rules', async () => {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/');
    const { findByText, asFragment } = render(<Router history={history}><SearchPage /></Router>);
    await findByText(/rules found/i);
    expect(asFragment()).toMatchSnapshot();
});

