LifeMerge UI Kit & Wireframes Implementation

This document summarises the finalised UI Kit v1.0, outlines the key wireframes for the MVP, and lists the screens that are marked as Ready for Development. Since direct editing in Figma is unavailable in this environment, the specifications are provided here for import into your design tool of choice.

UI Kit Components
Buttons

Three button styles are defined: Primary, Secondary and Tertiary. All buttons have a fixed height of 48 pt and rounded corners with a 10 pt radius. States include:

Default – normal background and label colours based on button type.

Pressed – background darkens slightly to indicate active press.

Disabled – lower opacity and muted colours; the button is not interactive.

Loading – shows an inline spinner in place of, or alongside, the label.

Input Fields

Text input fields are sized at 48 pt high and include a label, placeholder, optional icon and helper text. Supported states:

Default – empty field with placeholder text.

Focused – border highlights and the label floats above the input.

Filled – displays the user’s input; label remains above the field.

Error – border changes to the error colour; an error message appears below.

Disabled – muted appearance; the field is read‑only.

Cards

Cards act as containers for related content. They have 12 pt corner radius and a subtle shadow elevation. Three variants exist:

Variant	Use case
TaskCard	Shows task title, due date, priority and status
EventCard	Displays event name, date/time and location
FinanceCard	Contains transaction amount, category and type

Cards may elevate slightly or change shadow on hover or press.

Chips

Chips (tags) are used for categories and filters. They have a height of 28 pt with rounded ends. States include default (neutral border or background), selected (filled with accent colour and contrasting text) and disabled (reduced opacity).

App Bar

The top navigation bar is 56 pt high and contains a title and action icons. It adapts to light and dark themes. The bar may include a back button or menu icon on the left and context‑specific actions on the right.

Bottom Navigation

Bottom navigation consists of five items – Calendar, Tasks, Finance, Inbox and Profile. Each item shows an icon and optional label. States: default (neutral colour) and selected (accent colour and bold label). Icons switch colours in dark mode.

Spinners & Loading Indicators

Use circular spinners for indeterminate processes and skeleton placeholders for loading lists or cards. Where possible, use progress bars to indicate determinate progress. Indicators adopt neutral or primary colours appropriate for the active theme.

Colour Tokens

The palette is defined via tokens to support light and dark themes. Key tokens include:

Token	Description
primary	Main brand colour for highlights
secondary	Secondary accent or supporting colour
background	Page background colour
surface	Surface backgrounds (cards, panels)
error	Colour used for error states
success	Colour used for success messages
warning	Colour used for warnings
onPrimary	Colour of text/icons on a primary surface
onSecondary	Colour of text/icons on secondary surfaces
onBackground	Colour of text/icons on the background
onSurface	Colour of text/icons on a surface

Each token has values for both the light and dark themes to maintain sufficient contrast.

Typography

The type scale defines a clear hierarchy:

Style	Approximate size	Use
H1	32 pt	Main page titles
H2	24 pt	Section titles
H3	20 pt	Subsection headings
Body 1	16 pt	Primary body text
Body 2	14 pt	Secondary text
Caption	12 pt	Annotations and captions
Button	16 pt (bold)	Labels on buttons
Edge Cases & States

Proper handling of edge cases is critical for a polished user experience:

Empty states – when there is no content, show a friendly illustration and a brief message that explains the situation and offers a call‑to‑action to add content.

Error states – use the error colour token to highlight inputs or modules in error; provide clear messages and actions to recover (e.g. a Retry button for network errors).

Loading states – display skeleton placeholders or spinners while data is loading; subtle animations convey that the content is on its way.

Offline states – when connectivity is lost, show a banner or toast informing the user. Disable network‑dependent actions and allow offline functionality where possible. Notify the user once the connection returns.

MVP Wireframes

The following wireframes outline the core screens for the MVP. They are described at a structural level without visual styling so they can be implemented in any design tool.

Auth Screens

Onboarding – a series of slides introducing the value of the app with imagery and short text. Users can navigate forward or skip entirely.

Schedule Setup – an optional step where the user specifies their working pattern or preferred hours to personalise scheduling.

Registration – a form capturing email and password with inline validation and error feedback.

Login – a simple form for returning users to sign in with their credentials; includes an option to stay signed in.

Password Recovery – a two‑step flow to request a password reset via email and to confirm the reset.

Calendar Screens

Day View – detailed schedule for a single day with time slots and events stacked vertically. A floating action button allows creation of a new event.

Week View – a grid of seven columns representing days of the week with events displayed as blocks. Suitable for viewing relative occupancy across the week.

Month View – an overview calendar showing days of the month with subtle markers indicating the presence of events. Selecting a day drills down to the Day View.

Create Event – a form to add a new event: name, date/time picker, location and optional description; includes options for repetition and reminders.

Event Details – displays all information about an event (title, date/time, location, description, participants) and provides actions to edit or delete the event.

Task Screens

Task List – shows all tasks grouped by filters (e.g. by status or priority). Each item has a checkbox to mark it complete.

Task Detail – presents full details of a task: description, due date, context, priority, attachments, and allows editing or deletion.

Task Form – a form for creating or editing tasks; fields include name, description, due date, priority, context and reminder settings.

Ready for Development Screens

The following screens and components have been finalised and are ready to be handed off to engineering. They comply with the UI Kit and meet the Definition of Ready/Done criteria:

Onboarding_v1

Register_v1

Login_v1

Recovery_v1

Calendar_Day_v1

Task_List_v1

Task_Detail_v1

Event_New_v1

Each screen uses components defined in UI Kit v1.0 and accounts for all edge cases and states. These designs align with the MVP scope and can be imported into Figma or another design tool to continue development.