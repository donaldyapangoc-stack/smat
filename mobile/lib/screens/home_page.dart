import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';
import 'add_estacion.dart';

// ─── Umbrales SMAT (deben coincidir con sensor_emitter.py) ───────────────────
const double _UMBRAL_CRITICO = 70.0;   // Alerta de desborde (Lab 9.1)
const double _UMBRAL_ALERTA  = 20.0;   // Nivel de alerta intermedio
const double _UMBRAL_NORMAL  = 10.0;   // Por encima → modo precaución
// ─────────────────────────────────────────────────────────────────────────────

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late Future<List<Estacion>> futureEstaciones;
  final ApiService _apiService = ApiService();

  // Auto-refresh: refresca la lista automáticamente para ver cómo
  // las lecturas del IoT emulado aparecen solas (Integración Semana 9).
  Timer? _autoRefreshTimer;
  bool _hayAlertaCritica = false;   // controla el banner de emergencia

  @override
  void initState() {
    super.initState();
    _cargarEstaciones();
    // Refresca cada 3 segundos para capturar el modo emergencia (2 s del IoT)
    _autoRefreshTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _refreshData(),
    );
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    super.dispose();
  }

  void _cargarEstaciones() {
    futureEstaciones = _apiService.fetchEstaciones();
  }

  void _refreshData() {
    setState(() {
      _cargarEstaciones();
    });
  }

  // ── Devuelve el color del ícono según la última lectura ───────────────────
  // Umbrales actualizados para reflejar el reto del Lab 9.1:
  //   > 70 cm → CRÍTICO (rojo intenso)
  //   > 20 cm → PELIGRO (rojo)
  //   > 10 cm → ALERTA  (naranja)
  //   ≤ 10 cm → NORMAL  (verde)
  Future<Color> _getIconColor(int estacionId) async {
    double? ultimaLectura = await _apiService.getUltimaLectura(estacionId);
    if (ultimaLectura == null) return Colors.grey;
    if (ultimaLectura > _UMBRAL_CRITICO) return Colors.red.shade900;
    if (ultimaLectura > _UMBRAL_ALERTA)  return Colors.red;
    if (ultimaLectura > _UMBRAL_NORMAL)  return Colors.orange;
    return Colors.green;
  }

  // ── Retorna true si ALGUNA estación supera el umbral crítico ─────────────
  Future<bool> _verificarAlertaCritica(List<Estacion> estaciones) async {
    for (final e in estaciones) {
      final v = await _apiService.getUltimaLectura(e.id);
      if (v != null && v > _UMBRAL_CRITICO) return true;
    }
    return false;
  }

  // Diálogo para editar estación
  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Editar Estación"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nombreCtrl,
              decoration: const InputDecoration(labelText: "Nombre"),
            ),
            TextField(
              controller: ubicacionCtrl,
              decoration: const InputDecoration(labelText: "Ubicación"),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () async {
              bool ok = await _apiService.editarEstacion(
                estacion.id,
                nombreCtrl.text,
                ubicacionCtrl.text,
              );
              if (ok) {
                Navigator.pop(context);
                _refreshData();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Estación actualizada')),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Error al actualizar')),
                );
              }
            },
            child: const Text("Guardar"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // ── Fondo rojo suave cuando hay alerta crítica (Lab 9.1) ──────────────
      backgroundColor: _hayAlertaCritica
          ? Colors.red.shade50
          : Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        // El AppBar también cambia de color en modo emergencia
        backgroundColor: _hayAlertaCritica ? Colors.red.shade700 : null,
        title: Row(
          children: [
            const Text('Estaciones SMAT'),
            if (_hayAlertaCritica) ...[
              const SizedBox(width: 8),
              const Icon(Icons.warning_amber_rounded,
                  color: Colors.white, size: 20),
            ],
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().logout();
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );
            },
          )
        ],
      ),
      body: Column(
        children: [
          // ── Banner de emergencia (solo visible cuando hay lectura > 70) ──
          if (_hayAlertaCritica)
            Container(
              width: double.infinity,
              color: Colors.red.shade700,
              padding:
                  const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
              child: const Row(
                children: [
                  Icon(Icons.flood, color: Colors.white),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '🚨 ALERTA: Umbral de inundación superado (> 70 cm)',
                      style: TextStyle(
                          color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),

          // ── Lista de estaciones ──────────────────────────────────────────
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async {
                _refreshData();
                await Future.delayed(const Duration(seconds: 1));
              },
              child: FutureBuilder<List<Estacion>>(
                future: futureEstaciones,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(child: CircularProgressIndicator());
                  } else if (snapshot.hasError) {
                    return Center(
                      child: Text('❌ Error de conexion: ${snapshot.error}'),
                    );
                  } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                    return const Center(
                      child: Text('No hay estaciones'),
                    );
                  } else {
                    // Verificar si alguna estación está en modo crítico
                    _verificarAlertaCritica(snapshot.data!).then((critica) {
                      if (critica != _hayAlertaCritica) {
                        setState(() => _hayAlertaCritica = critica);
                      }
                    });

                    return ListView.builder(
                      itemCount: snapshot.data!.length,
                      itemBuilder: (context, index) {
                        final estacion = snapshot.data![index];

                        return Dismissible(
                          key: Key(estacion.id.toString()),
                          direction: DismissDirection.endToStart,
                          background: Container(
                            color: Colors.red,
                            alignment: Alignment.centerRight,
                            padding: const EdgeInsets.only(right: 20),
                            child:
                                const Icon(Icons.delete, color: Colors.white),
                          ),
                          onDismissed: (direction) async {
                            bool ok = await _apiService
                                .eliminarEstacion(estacion.id);
                            if (ok) {
                              _refreshData();
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                    content:
                                        Text('${estacion.nombre} eliminada')),
                              );
                            } else {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text('Error al eliminar')),
                              );
                            }
                          },
                          child: FutureBuilder<Color>(
                            future: _getIconColor(estacion.id),
                            builder: (context, colorSnapshot) {
                              final color =
                                  colorSnapshot.data ?? Colors.grey;
                              final esCritico =
                                  color == Colors.red.shade900;

                              return ListTile(
                                // Fondo rojo translúcido en filas críticas
                                tileColor: esCritico
                                    ? Colors.red.shade100
                                    : null,
                                leading: Icon(
                                  Icons.satellite_alt,
                                  color: color,
                                ),
                                title: Text(
                                  estacion.nombre,
                                  style: TextStyle(
                                    fontWeight: esCritico
                                        ? FontWeight.bold
                                        : FontWeight.normal,
                                    color: esCritico
                                        ? Colors.red.shade900
                                        : null,
                                  ),
                                ),
                                subtitle: Text(estacion.ubicacion),
                                // Chip de estado
                                trailing: esCritico
                                    ? Chip(
                                        label: const Text('CRÍTICO',
                                            style: TextStyle(
                                                color: Colors.white,
                                                fontSize: 11)),
                                        backgroundColor:
                                            Colors.red.shade700,
                                        padding: EdgeInsets.zero,
                                      )
                                    : null,
                                onTap: () =>
                                    _mostrarDialogoEdicion(estacion),
                              );
                            },
                          ),
                        );
                      },
                    );
                  }
                },
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => AddEstacionScreen()),
          );
          if (result == true) {
            _refreshData();
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}