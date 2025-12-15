import 'package:flutter/material.dart';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});

  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  final List<_Transaction> _transactions = <_Transaction>[
    _Transaction(
      title: 'Подписка LifeMerge',
      amount: -1299,
      category: 'Подписки',
      date: DateTime.now(),
      recurring: true,
    ),
    _Transaction(
      title: 'Проект: оплата клиента',
      amount: 48000,
      category: 'Доход',
      date: DateTime.now().subtract(const Duration(days: 1)),
    ),
    _Transaction(
      title: 'Кофе по дороге',
      amount: -320,
      category: 'Питание',
      date: DateTime.now().subtract(const Duration(days: 2)),
      linkedToCalendar: true,
    ),
  ];

  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  String _title = '';
  double _amount = 0;
  String _category = 'Питание';
  DateTime _date = DateTime.now();
  bool _recurring = false;
  bool _linkToCalendar = false;

  void _addTransaction() {
    final isValid = _formKey.currentState?.validate() ?? false;
    if (!isValid) return;
    _formKey.currentState?.save();

    setState(() {
      _transactions.insert(
        0,
        _Transaction(
          title: _title,
          amount: _amount,
          category: _category,
          date: _date,
          recurring: _recurring,
          linkedToCalendar: _linkToCalendar,
        ),
      );
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Транзакция "$_title" сохранена')),
    );
  }

  double get _balance => _transactions.fold(0, (sum, t) => sum + t.amount);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final expenses = _transactions.where((t) => t.amount < 0).fold<double>(0, (sum, t) => sum + t.amount);
    final income = _transactions.where((t) => t.amount > 0).fold<double>(0, (sum, t) => sum + t.amount);
    final monthlyBudget = 60000;
    final progress = (income + expenses).clamp(0, monthlyBudget) / monthlyBudget;

    return Scaffold(
      appBar: AppBar(title: const Text('Финансы')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: <Widget>[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        const Icon(Icons.account_balance_wallet_outlined),
                        const SizedBox(width: 8),
                        Text('Баланс за месяц', style: theme.textTheme.titleMedium),
                        const Spacer(),
                        Text('${_balance.toStringAsFixed(0)} ₽', style: theme.textTheme.headlineSmall),
                      ],
                    ),
                    const SizedBox(height: 12),
                    LinearProgressIndicator(value: progress),
                    const SizedBox(height: 4),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text('Бюджет: $monthlyBudget ₽', style: theme.textTheme.bodySmall),
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 12,
                      children: <Widget>[
                        Chip(
                          avatar: const Icon(Icons.call_made, size: 18),
                          label: Text('Доход: ${income.toStringAsFixed(0)} ₽'),
                        ),
                        Chip(
                          avatar: const Icon(Icons.call_received, size: 18),
                          label: Text('Расходы: ${expenses.toStringAsFixed(0)} ₽'),
                        ),
                        Chip(
                          avatar: const Icon(Icons.repeat, size: 18),
                          label: Text('Регулярки: ${_transactions.where((t) => t.recurring).length}'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            ExpansionTile(
              initiallyExpanded: true,
              leading: const Icon(Icons.add_card),
              title: const Text('Добавить операцию'),
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      children: <Widget>[
                        TextFormField(
                          decoration: const InputDecoration(labelText: 'Описание'),
                          onSaved: (value) => _title = value?.trim() ?? '',
                          validator: (value) => value == null || value.isEmpty ? 'Обязательное поле' : null,
                        ),
                        const SizedBox(height: 8),
                        TextFormField(
                          decoration: const InputDecoration(labelText: 'Сумма, ₽ (отрицательная = расход)'),
                          keyboardType: TextInputType.number,
                          onSaved: (value) => _amount = double.tryParse(value ?? '0') ?? 0,
                          validator: (value) => value == null || value.isEmpty ? 'Укажите сумму' : null,
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          decoration: const InputDecoration(labelText: 'Категория'),
                          value: _category,
                          items: const <String>['Питание', 'Транспорт', 'Доход', 'Подписки', 'Дом']
                              .map((c) => DropdownMenuItem<String>(value: c, child: Text(c)))
                              .toList(),
                          onChanged: (value) => setState(() => _category = value ?? _category),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () async {
                                  final picked = await showDatePicker(
                                    context: context,
                                    firstDate: DateTime.now().subtract(const Duration(days: 365)),
                                    lastDate: DateTime.now().add(const Duration(days: 365)),
                                    initialDate: _date,
                                  );
                                  if (picked != null) {
                                    setState(() => _date = picked);
                                  }
                                },
                                icon: const Icon(Icons.event),
                                label: Text('Дата: ${MaterialLocalizations.of(context).formatMediumDate(_date)}'),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        SwitchListTile(
                          title: const Text('Регулярная операция'),
                          value: _recurring,
                          onChanged: (value) => setState(() => _recurring = value),
                        ),
                        SwitchListTile(
                          title: const Text('Привязать к календарю'),
                          subtitle: const Text('Создать событие с суммой и категорией'),
                          value: _linkToCalendar,
                          onChanged: (value) => setState(() => _linkToCalendar = value),
                        ),
                        const SizedBox(height: 8),
                        Align(
                          alignment: Alignment.centerRight,
                          child: FilledButton.icon(
                            icon: const Icon(Icons.save),
                            label: const Text('Сохранить'),
                            onPressed: _addTransaction,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.separated(
                itemCount: _transactions.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final tx = _transactions[index];
                  final color = tx.amount >= 0 ? Colors.green : theme.colorScheme.error;
                  return ListTile(
                    tileColor: theme.colorScheme.surfaceVariant.withOpacity(0.3),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    leading: CircleAvatar(
                      backgroundColor: color.withOpacity(0.15),
                      child: Icon(tx.amount >= 0 ? Icons.call_made : Icons.call_received, color: color),
                    ),
                    title: Text(tx.title),
                    subtitle: Text(
                      '${tx.category} · ${MaterialLocalizations.of(context).formatShortDate(tx.date)}'
                      '${tx.recurring ? ' · повтор' : ''}'
                      '${tx.linkedToCalendar ? ' · в календаре' : ''}',
                    ),
                    trailing: Text('${tx.amount.toStringAsFixed(0)} ₽', style: TextStyle(color: color)),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Transaction {
  _Transaction({
    required this.title,
    required this.amount,
    required this.category,
    required this.date,
    this.recurring = false,
    this.linkedToCalendar = false,
  });

  final String title;
  final double amount;
  final String category;
  final DateTime date;
  final bool recurring;
  final bool linkedToCalendar;
}
