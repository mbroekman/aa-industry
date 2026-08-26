# Show Corp Jobs in Personal Dashboard

We will update the Personal Industry Dashboard to also display Corporation Industry Jobs that were installed by the user's characters. A filter will be added to toggle between showing 'All', 'Personal', and 'Corp' jobs.

## Proposed Changes

### industry_reforged/views/dashboard.py

- Fetch `CharacterIndustryJob` as usual, but annotate each with `job_type = 'Personal'`.
- Fetch `CorporationIndustryJob` where `installer_id__in=user_characters`, select related `installer`, and annotate each with `character = j.installer` and `job_type = 'Corp'`.
- Combine both querysets into a single list and sort it descending by `end_date`.
- The existing logic that splits jobs into active/history and manufacturing/research will seamlessly handle the combined list.

### industry_reforged/templates/industry_reforged/personal_dashboard.html

#### Manufacturing Tab

- Add a dropdown filter for "Ownership" (All / Personal / Corp).
- Add an "Ownership" column to the `personal-jobs-active-table` and `personal-jobs-history-table`.
- Update the DataTables initialization script to attach an `on('change')` event for the new dropdown, filtering the "Ownership" column.

#### Research Tab

- Add a similar dropdown filter for "Ownership" at the top of the Research tab.
- Add `data-job-type="{{ job.job_type }}"` to each job row (`<tr>`) in the active and history research tables.
- Add a small jQuery script to hide/show these rows based on the dropdown selection.
- Add a badge in the Activity column or a separate small column to indicate Personal/Corp for research jobs.

## Verification Plan

- Reload the Personal Dashboard view in the browser.
- Verify that corp jobs started by the user appear in both Manufacturing and Research tabs.
- Verify that the Ownership dropdowns correctly filter the tables to show only Personal or only Corp jobs.
- Update the backlog task upon completion.
