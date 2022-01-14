import React from 'react';
import fs from 'fs';
import path from 'path';
import { render } from '@testing-library/react';
import { RulePage } from '../RulePage';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { fetchMock } from '../testutils'

const rulesPath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'plugin_rules');

function readRuleFile(ruleId, filename) {
    return fs.readFileSync(path.join(rulesPath, ruleId, filename)).toString();
}

beforeEach(() => {
    const specS1000 = readRuleFile('S1000', 'cfamily-description.html');
    const metadataS1000 = readRuleFile('S1000', 'cfamily-metadata.json');
    const specS3457 = readRuleFile('S3457', 'csharp-description.html');
    const metadataS3457 = readRuleFile('S3457', 'csharp-metadata.json');
    const rootUrl = process.env.PUBLIC_URL;
    let mockUrls = {};
    mockUrls[`${rootUrl}/rules/S1000/cfamily-description.html`] = {text: specS1000};
    mockUrls[`${rootUrl}/rules/S1000/cfamily-metadata.json`] = {json: JSON.parse(metadataS1000)};
    mockUrls[`${rootUrl}/rules/S3457/csharp-description.html`] = {text: specS3457};
    mockUrls[`${rootUrl}/rules/S3457/csharp-metadata.json`] = {json: JSON.parse(metadataS3457)};
    mockUrls[`${rootUrl}/rules/S3457/default-description.html`] = {text: specS3457};
    mockUrls[`${rootUrl}/rules/S3457/default-metadata.json`] = {json: JSON.parse(metadataS3457)};
    mockUrls[`${rootUrl}/covered_rules.json`] = {json:
        {'ABAP': {'S100': 'ver1', 'S200': 'ver2'},
        'CSH' : {'S3457': 'c#1'},
        'C': {'S100': 'c1', 'S234': {'since': 'c2', 'until': 'c3'}}}
    };
    jest.spyOn(global, 'fetch').mockImplementation(fetchMock(mockUrls));
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
