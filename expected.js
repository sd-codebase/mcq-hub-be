const interviewQuestionSamples = [
	{
		question: 'What are the main differences between var, let, and const?',
		answer:
			"## Main Differences\n\nThe main differences are:\n\n### 1. **Scope**\n- `var` is **function-scoped**\n- `let` and `const` are **block-scoped**\n\n```javascript\nfunction test() {\n  if (true) {\n    var x = 1;  // Function-scoped\n    let y = 2;  // Block-scoped\n  }\n  console.log(x); // 1 (accessible)\n  console.log(y); // ReferenceError\n}\n```\n\n### 2. **Hoisting**\n- All three are hoisted\n- `var` is initialized with `undefined`\n- `let` and `const` remain in the **Temporal Dead Zone** until declaration\n\n### 3. **Redeclaration**\n- `var` allows redeclaration in the same scope\n- `let` and `const` don't allow redeclaration\n\n### 4. **Reassignment**\n- `var` and `let` allow reassignment\n- `const` doesn't allow reassignment\n\n### 5. **Initialization**\n- `var` and `let` can be declared without initialization\n- `const` must be initialized at declaration",
		explanation:
			'Understanding these differences is **crucial** for writing modern JavaScript. `const` should be your default choice, followed by `let` when reassignment is needed. `var` should generally be avoided in modern code due to its confusing scoping rules.',
	},
	{
		question:
			'What is the difference between null and undefined in TypeScript?',
		answer:
			'## null vs undefined\n\n### Conceptual Difference\n\n- **undefined** - Variable declared but not initialized, or property doesn\'t exist\n- **null** - Intentional absence of value, explicitly assigned\n\n### Examples\n\n```typescript\n// undefined - not initialized\nlet x: number;\nconsole.log(x); // undefined\n\n// null - intentionally empty\nlet user: string | null = null;\n```\n\n### Type System Differences\n\n**1. Without strictNullChecks**\n```typescript\nlet name: string = null; // ✅ Allowed\nlet age: number = undefined; // ✅ Allowed\n```\n\n**2. With strictNullChecks** (recommended)\n```typescript\nlet name: string = null; // ❌ Error\nlet name: string | null = null; // ✅ Correct\n\nlet age: number = undefined; // ❌ Error\nlet age: number | undefined = undefined; // ✅ Correct\n```\n\n### typeof Behavior\n\n```typescript\nconsole.log(typeof null); // "object" (JavaScript quirk!)\nconsole.log(typeof undefined); // "undefined"\n```\n\n### Equality Comparisons\n\n```typescript\nnull == undefined;  // true (loose equality)\nnull === undefined; // false (strict equality)\n\nnull == null;  // true\nnull === null; // true\n```\n\n### Best Practices\n\n```typescript\n// Use undefined for uninitialized\nlet value: string | undefined;\n\n// Use null for intentionally empty\nlet selectedUser: User | null = null;\n\n// Optional parameters use undefined\nfunction greet(name?: string) {\n  // name is string | undefined\n}\n```',
		explanation:
			'Understanding the distinction is **crucial for strict type checking**. `undefined` typically means "not yet set", while `null` means "intentionally empty". Always use `strictNullChecks` in production code.',
	},
];

const outputQuestionSample = [
	{
		question:
			'```typescript\nlet age: number = 25;\nlet price: number = 99.99;\nconsole.log(typeof age, typeof price);\n```',
		output: '```\nnumber number\n```',
		explanation:
			"In TypeScript (and JavaScript), both integers and floating-point numbers are of type `number`. There's no separate integer type.",
	},
	{
		question:
			'```typescript\nlet data: undefined = undefined;\nconsole.log(typeof data);\n```',
		output: '```\nundefined\n```',
		explanation:
			'The `typeof` operator correctly identifies `undefined` as `"undefined"`. This is the expected behavior for variables that are explicitly set to undefined.',
	},
	{
		question:
			'```javascript\nlet obj1 = { x: 1 };\nlet obj2 = obj1;\nobj2.x = 2;\nconsole.log(obj1.x);\n```',
		output: '```\n2\n```',
		explanation:
			'**Objects are copied by reference**. `obj2 = obj1` makes both variables reference the **same object** in memory. Modifying through `obj2` affects `obj1`.\n\n**Visual representation:**\n```\nobj1 → { x: 1 } ← obj2 (same object)\nobj2.x = 2\nobj1 → { x: 2 } ← obj2 (still same object)\n```',
	},
];

const mcaQuestionsSample = [
	{
		question:
			'What is the scope of a variable declared with `var` inside a function?',
		options: ['Global scope', 'Block scope', 'Function scope', 'Module scope'],
		correctAnswer: 2,
		explanation:
			'Variables declared with `var` are **function-scoped**, meaning they are accessible throughout the entire function in which they are declared, regardless of block boundaries.',
	},
	{
		question:
			'What is the difference between `null` and `undefined` in TypeScript?',
		options: [
			'They are exactly the same',
			"null means 'no value', undefined means 'not yet assigned'",
			'null is a number, undefined is a string',
			'There is no difference in strict mode',
		],
		correctAnswer: 1,
		explanation:
			'`null` represents an intentional absence of value, while `undefined` typically means a variable has been declared but not yet assigned a value. They are distinct types in TypeScript.',
	},
];
