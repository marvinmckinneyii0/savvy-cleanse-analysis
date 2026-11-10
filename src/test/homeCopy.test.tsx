import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AnalysisTypes from '@/components/AnalysisTypes';
import CTA from '@/components/CTA';
import DataFlow from '@/components/DataFlow';
import Features from '@/components/Features';
import Hero from '@/components/Hero';
import SignupForm from '@/components/SignupForm';

/**
 * The concierge beta is a done-for-you service: a person runs SAINT on a
 * customer's CSV and sends back a report. These home sections must not
 * describe things that do not exist yet.
 */
const NOT_OFFERED = [
  /upload your files/i,
  /\b(json|xlsx|xml|txt)\b/i,
  /jupyter|notebook|\.ipynb/i,
  /python|pandas|numpy|scikit/i,
  /dashboard/i,
  /charts?\b|plots?\b|visuali[sz]ations?/i,
  /predictive|prescriptive|forecast/i,
  /optimi[sz]ation|scenario simulation|hypothesis testing|causal/i,
  /waitlist|early access/i,
  /unstructured/i,
  /sign in|sign up|signing up|free trial/i,
  /\bapi\b/i,
];

const renderHomeSections = () =>
  render(
    <MemoryRouter>
      <Hero />
      <Features />
      <AnalysisTypes />
      <DataFlow />
      <CTA />
      <SignupForm />
    </MemoryRouter>,
  );

describe('home page copy for the concierge beta', () => {
  it.each(NOT_OFFERED)('does not mention %s', (pattern) => {
    const { container } = renderHomeSections();

    expect(container.textContent).not.toMatch(pattern);
  });

  it('describes the real request-and-deliver flow', () => {
    const { container } = renderHomeSections();
    const text = container.textContent ?? '';

    expect(text).toMatch(/no file upload on this site/i);
    expect(text).toMatch(/CSV only, up to 100 MB/);
    expect(text).toMatch(/delete your file 7 days after delivery/i);
    expect(text).toMatch(/health records, financial account data or government IDs/);
    expect(text).toMatch(/Word or PDF/);
  });

  it('states that cleaning is optional and leaves the original unchanged', () => {
    const { container } = renderHomeSections();
    const text = container.textContent ?? '';

    expect(text).toMatch(/Cleaning is off unless you ask for it/);
    expect(text).toMatch(/keeps your original file unchanged/);
  });

  it('offers the report request as the primary action', () => {
    renderHomeSections();

    expect(
      screen.getAllByRole('button', { name: 'Request a Data-Quality Report' }).length,
    ).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole('button', { name: 'Request Report' })).toBeInTheDocument();
  });
});
