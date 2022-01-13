import React from 'react';
import fs from 'fs';
import path from 'path';
import { render } from '@testing-library/react';
import { RulePage } from '../RulePage';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';

beforeEach(() => {
    const rulesPath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'plugin_rules');
    const specS1000 = fs.readFileSync(path.join(rulesPath, 'S1000', 'cfamily-description.html')).toString();
    const metadataS1000 = fs.readFileSync(path.join(rulesPath, 'S1000', 'cfamily-metadata.json')).toString();
    const specS3457 = fs.readFileSync(path.join(rulesPath, 'S3457', 'csharp-description.html')).toString();
    const metadataS3457 = fs.readFileSync(path.join(rulesPath, 'S3457', 'csharp-metadata.json')).toString();
    function fetchMock(url, opts) {
        const coveredRulesUrl = `${process.env.PUBLIC_URL}/covered_rules.json`;
        const specUrlS1000 = `${process.env.PUBLIC_URL}/rules/S1000/cfamily-description.html`;
        const metadataUrlS1000 = `${process.env.PUBLIC_URL}/rules/S1000/cfamily-metadata.json`;
        const specUrlS3457 = `${process.env.PUBLIC_URL}/rules/S3457/csharp-description.html`;
        const metadataUrlS3457 = `${process.env.PUBLIC_URL}/rules/S3457/csharp-metadata.json`;
        const specUrlS3457Generic = `${process.env.PUBLIC_URL}/rules/S3457/default-description.html`;
        const metadataUrlS3457Generic = `${process.env.PUBLIC_URL}/rules/S3457/default-metadata.json`;
        if (url === specUrlS1000) {
            return Promise.resolve({text: () => Promise.resolve(specS1000)});
        } else if (url === metadataUrlS1000) {
            return Promise.resolve({json: () => Promise.resolve(JSON.parse(metadataS1000))});
        } if (url === specUrlS3457) {
            return Promise.resolve({text: () => Promise.resolve(specS3457)});
        } else if (url === metadataUrlS3457) {
            return Promise.resolve({json: () => Promise.resolve(JSON.parse(metadataS3457))});
        } if (url === specUrlS3457Generic) {
            return Promise.resolve({text: () => Promise.resolve(specS3457)});
        } else if (url === metadataUrlS3457Generic) {
            return Promise.resolve({json: () => Promise.resolve(JSON.parse(metadataS3457))});
        } else if (url === coveredRulesUrl) {
            return Promise.resolve({json: () => Promise.resolve({'ABAP': {'S100': 'ver1', 'S200': 'ver2'},
                                                                 'CSH' : {'S3457': 'c#1'},
                                                                 'C': {'S100': 'c1', 'S234': {'since': 'c2',
                                                                                              'until': 'c3'}}})});
        } else {
            return Promise.reject('unexpected url ' + url);
        }
    }
    jest.spyOn(global, 'fetch').mockImplementation(fetchMock);
});

afterEach(() => {
    global.fetch.mockClear();
});

test('renders cfamily version of S1000', async () => {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/S1000/cfamily');
    const match = {params: {ruleid: "S1000", language: "cfamily"}};
    const { findByText, asFragment } = render(<Router history={history}>
        <RulePage match={match} />
    </Router>);
    await findByText(/S1000/);
    await findByText(/Implementation tickets on Jira/);
    // some random phrase from the rule specification
    await findByText(/7-3-3 - There shall be no unnamed namespaces in header files./);
    expect(asFragment()).toMatchSnapshot();
});

test('renders C# version of S3457 (using GH for issues instead of Jira)', async () => {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/S3457/csharp');
    const match = {params: {ruleid: "S3457", language: "csharp"}};
    const { findByText, asFragment } = render(<Router history={history}>
        <RulePage match={match} />
    </Router>);
    await findByText(/S3457/);
    await findByText(/Implementation issues on GitHub/);
    expect(asFragment()).toMatchSnapshot();
});

test('renders generic version of S3457', async () => {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/S3457');
    const match = {params: {ruleid: "S3457"}};
    const { findAllByText, asFragment } = render(<Router history={history}>
        <RulePage match={match} />
    </Router>);
    await findAllByText(/S3457/);
    await findAllByText(/cfamily/);
    await findAllByText(/csharp/);
    expect(asFragment()).toMatchSnapshot();
});
