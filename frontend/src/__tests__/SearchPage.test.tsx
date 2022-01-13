import React from 'react';
import path from 'path';
import { render } from '@testing-library/react';
import { SearchPage } from '../SearchPage';
import { buildIndexStore, buildSearchIndex } from '../deployment/searchIndex';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';

beforeEach(() => {
    const rulePath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'plugin_rules');
    const [indexStore, indexAggregates] = buildIndexStore(rulePath);
    const searchIndex = buildSearchIndex(indexStore);
    function fetchMock(url, opts) {
        const indexUrl = `${process.env.PUBLIC_URL}/rules/rule-index.json`;
        const storeDataUrl = `${process.env.PUBLIC_URL}/rules/rule-index-store.json`;
        const aggregatesUrl = `${process.env.PUBLIC_URL}/rules/rule-index-aggregates.json`;
        const coveredRulesUrl = `${process.env.PUBLIC_URL}/covered_rules.json`;
        return Promise.resolve({
            json: () => {
                if (url === indexUrl) {
                    return Promise.resolve(JSON.parse(JSON.stringify(searchIndex)));
                } else if (url === storeDataUrl) {
                    return Promise.resolve(JSON.parse(JSON.stringify(indexStore)));
                } else if (url === aggregatesUrl) {
                    return Promise.resolve(JSON.parse(JSON.stringify(indexAggregates)));
                } else if (url === coveredRulesUrl) {
                    return Promise.resolve({'ABAP': {'S100': 'ver1', 'S200': 'ver2'},
                                            'C': {'S100': 'c1', 'S234': {'since': 'c2',
                                                                         'until': 'c3'}}});
                } else {
                    return Promise.reject('unexpected url ' + url);
                }
            }
        })
    }
    jest.spyOn(global, 'fetch').mockImplementation(fetchMock);
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

