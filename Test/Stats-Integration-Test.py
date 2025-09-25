#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Integration Test
Prueba de integración para los nuevos endpoints de estadísticas del sistema

Este test verifica:
1. Endpoint de estadísticas de usuarios (/users/stats)
2. Endpoint de estadísticas de tareas (/tasks/stats)
3. Integración entre ambos servicios
4. Métricas de productividad
5. Limpieza automática de datos de prueba
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the Test directory to Python path to import test utilities
sys.path.append(os.path.join(os.path.dirname(__file__)))
from test_utils import TestDataTracker, PDFReportGenerator

class StatsIntegrationTest:
    def __init__(self):
        self.base_url_users = "http://localhost:5001"
        self.base_url_tasks = "http://localhost:5002"
        self.tracker = TestDataTracker()
        self.test_results = []
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_symbol = "✅" if status == "PASSED" else "❌"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def setup_test_data(self):
        """Create test users and tasks for statistics testing"""
        print("\n=== CONFIGURACIÓN DE DATOS DE PRUEBA ===")
        
        # Create test users
        test_users = [
            {"name": "Alice Statistics"},
            {"name": "Bob Analytics"}, 
            {"name": "Carol Metrics"},
            {"name": "David Dashboard"}
        ]
        
        created_users = []
        for user_data in test_users:
            try:
                response = requests.post(f"{self.base_url_users}/users", json=user_data, timeout=5)
                if response.status_code == 201:
                    user = response.json()
                    created_users.append(user)
                    self.tracker.track_user(user['id'])
                    print(f"✅ Usuario creado: {user['name']} (ID: {user['id']})")
                else:
                    print(f"❌ Error creando usuario {user_data['name']}: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión creando usuario {user_data['name']}: {str(e)}")
        
        # Create test tasks with different distribution
        test_tasks = [
            {"title": "Task 1 for Alice", "user_id": created_users[0]['id']},
            {"title": "Task 2 for Alice", "user_id": created_users[0]['id']},
            {"title": "Task 3 for Alice", "user_id": created_users[0]['id']},  # Alice gets 3 tasks
            {"title": "Task 1 for Bob", "user_id": created_users[1]['id']},
            {"title": "Task 2 for Bob", "user_id": created_users[1]['id']},    # Bob gets 2 tasks
            {"title": "Task 1 for Carol", "user_id": created_users[2]['id']},  # Carol gets 1 task
            # David gets 0 tasks for testing inactive users
        ]
        
        created_tasks = []
        for task_data in test_tasks:
            try:
                response = requests.post(f"{self.base_url_tasks}/tasks", json=task_data, timeout=5)
                if response.status_code == 201:
                    task = response.json()
                    created_tasks.append(task)
                    self.tracker.track_task(task['id'])
                    print(f"✅ Tarea creada: {task['title']} (ID: {task['id']})")
                else:
                    print(f"❌ Error creando tarea {task_data['title']}: {response.text}")
            except Exception as e:
                print(f"❌ Error de conexión creando tarea {task_data['title']}: {str(e)}")
        
        return created_users, created_tasks
    
    def test_user_stats_endpoint(self):
        """Test the /users/stats endpoint"""
        print("\n=== PRUEBA DE ESTADÍSTICAS DE USUARIOS ===")
        
        try:
            response = requests.get(f"{self.base_url_users}/users/stats", timeout=10)
            
            if response.status_code != 200:
                self.log_result("User Stats Endpoint", "FAILED", f"HTTP {response.status_code}: {response.text}")
                return False
            
            stats = response.json()
            
            # Verify required fields
            required_fields = ['timestamp', 'users', 'tasks', 'system']
            missing_fields = [field for field in required_fields if field not in stats]
            
            if missing_fields:
                self.log_result("User Stats Structure", "FAILED", f"Missing fields: {missing_fields}")
                return False
            
            # Verify users section
            if 'total_users' not in stats['users'] or 'recent_users' not in stats['users']:
                self.log_result("User Stats Users Section", "FAILED", "Missing users statistics")
                return False
            
            # Verify we have at least our test users
            if stats['users']['total_users'] < 4:
                self.log_result("User Stats Count", "FAILED", f"Expected at least 4 users, got {stats['users']['total_users']}")
                return False
            
            # Verify tasks section (from cross-service call)
            if 'total_tasks' not in stats['tasks']:
                self.log_result("User Stats Tasks Section", "FAILED", "Missing tasks statistics from cross-service call")
                return False
            
            # Verify system status
            if 'status' not in stats['system'] or 'services' not in stats['system']:
                self.log_result("User Stats System Section", "FAILED", "Missing system status")
                return False
            
            self.log_result("User Stats Endpoint", "PASSED", f"Total users: {stats['users']['total_users']}, Total tasks: {stats['tasks']['total_tasks']}")
            
            print(f"📊 User Statistics Summary:")
            print(f"   - Total Users: {stats['users']['total_users']}")
            print(f"   - Total Tasks: {stats['tasks']['total_tasks']}")
            print(f"   - Users with Tasks: {stats['tasks'].get('users_with_tasks', 'N/A')}")
            print(f"   - System Status: {stats['system']['status']}")
            
            return True
            
        except Exception as e:
            self.log_result("User Stats Endpoint", "FAILED", f"Exception: {str(e)}")
            return False
    
    def test_task_stats_endpoint(self):
        """Test the /tasks/stats endpoint"""
        print("\n=== PRUEBA DE ESTADÍSTICAS DE TAREAS ===")
        
        try:
            response = requests.get(f"{self.base_url_tasks}/tasks/stats", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Task Stats Endpoint", "FAILED", f"HTTP {response.status_code}: {response.text}")
                return False
            
            stats = response.json()
            
            # Verify required fields
            required_fields = ['timestamp', 'tasks', 'users', 'productivity_metrics', 'system']
            missing_fields = [field for field in required_fields if field not in stats]
            
            if missing_fields:
                self.log_result("Task Stats Structure", "FAILED", f"Missing fields: {missing_fields}")
                return False
            
            # Verify tasks section
            tasks_section = stats['tasks']
            required_task_fields = ['total_tasks', 'users_with_tasks', 'recent_tasks', 'top_productive_users']
            missing_task_fields = [field for field in required_task_fields if field not in tasks_section]
            
            if missing_task_fields:
                self.log_result("Task Stats Tasks Section", "FAILED", f"Missing task fields: {missing_task_fields}")
                return False
            
            # Verify we have our test tasks (should be at least 6)
            if tasks_section['total_tasks'] < 6:
                self.log_result("Task Stats Count", "FAILED", f"Expected at least 6 tasks, got {tasks_section['total_tasks']}")
                return False
            
            # Verify productivity metrics
            prod_metrics = stats['productivity_metrics']
            required_metrics = ['avg_tasks_per_user', 'avg_tasks_per_active_user']
            missing_metrics = [field for field in required_metrics if field not in prod_metrics]
            
            if missing_metrics:
                self.log_result("Task Stats Productivity Metrics", "FAILED", f"Missing metrics: {missing_metrics}")
                return False
            
            # Verify top productive users
            top_users = tasks_section['top_productive_users']
            if not isinstance(top_users, list) or len(top_users) == 0:
                self.log_result("Task Stats Top Users", "FAILED", "No top productive users found")
                return False
            
            # The first user should have 3 tasks (Alice)
            if top_users[0]['task_count'] != 3:
                self.log_result("Task Stats Top User Verification", "FAILED", f"Expected top user to have 3 tasks, got {top_users[0]['task_count']}")
                return False
            
            self.log_result("Task Stats Endpoint", "PASSED", f"Total tasks: {tasks_section['total_tasks']}, Active users: {tasks_section['users_with_tasks']}")
            
            print(f"📊 Task Statistics Summary:")
            print(f"   - Total Tasks: {tasks_section['total_tasks']}")
            print(f"   - Users with Tasks: {tasks_section['users_with_tasks']}")
            print(f"   - Avg Tasks per User: {prod_metrics['avg_tasks_per_user']}")
            print(f"   - Avg Tasks per Active User: {prod_metrics['avg_tasks_per_active_user']}")
            print(f"   - Top Productive User: User {top_users[0]['user_id']} with {top_users[0]['task_count']} tasks")
            
            return True
            
        except Exception as e:
            self.log_result("Task Stats Endpoint", "FAILED", f"Exception: {str(e)}")
            return False
    
    def test_cross_service_integration(self):
        """Test that both statistics endpoints provide consistent cross-service data"""
        print("\n=== PRUEBA DE INTEGRACIÓN ENTRE SERVICIOS ===")
        
        try:
            # Get stats from both services
            user_stats_response = requests.get(f"{self.base_url_users}/users/stats", timeout=10)
            task_stats_response = requests.get(f"{self.base_url_tasks}/tasks/stats", timeout=10)
            
            if user_stats_response.status_code != 200 or task_stats_response.status_code != 200:
                self.log_result("Cross-Service Integration", "FAILED", "Could not get stats from both services")
                return False
            
            user_stats = user_stats_response.json()
            task_stats = task_stats_response.json()
            
            # Verify consistent user count
            users_from_user_service = user_stats['users']['total_users']
            users_from_task_service = task_stats['users']['total_users']
            
            if users_from_user_service != users_from_task_service:
                self.log_result("Cross-Service User Count", "FAILED", 
                              f"Inconsistent user count: User service reports {users_from_user_service}, Task service reports {users_from_task_service}")
                return False
            
            # Verify consistent task count
            tasks_from_user_service = user_stats['tasks']['total_tasks']
            tasks_from_task_service = task_stats['tasks']['total_tasks']
            
            if tasks_from_user_service != tasks_from_task_service:
                self.log_result("Cross-Service Task Count", "FAILED", 
                              f"Inconsistent task count: User service reports {tasks_from_user_service}, Task service reports {tasks_from_task_service}")
                return False
            
            # Verify both services report healthy status
            user_service_status = user_stats['system']['status']
            task_service_status = task_stats['system']['status']
            
            if user_service_status != 'healthy' or task_service_status != 'healthy':
                self.log_result("Cross-Service Health Status", "FAILED", 
                              f"Services not healthy: User service: {user_service_status}, Task service: {task_service_status}")
                return False
            
            self.log_result("Cross-Service Integration", "PASSED", 
                          f"Consistent data - Users: {users_from_user_service}, Tasks: {tasks_from_task_service}")
            
            print(f"🔗 Cross-Service Integration Summary:")
            print(f"   - Both services report {users_from_user_service} users")
            print(f"   - Both services report {tasks_from_task_service} tasks")
            print(f"   - Both services report healthy status")
            
            return True
            
        except Exception as e:
            self.log_result("Cross-Service Integration", "FAILED", f"Exception: {str(e)}")
            return False
    
    def test_statistics_performance(self):
        """Test response time of statistics endpoints"""
        print("\n=== PRUEBA DE RENDIMIENTO DE ESTADÍSTICAS ===")
        
        try:
            import time
            
            # Test user stats performance
            start_time = time.time()
            response = requests.get(f"{self.base_url_users}/users/stats", timeout=5)
            user_stats_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_result("User Stats Performance", "FAILED", f"HTTP {response.status_code}")
                return False
            
            # Test task stats performance
            start_time = time.time()
            response = requests.get(f"{self.base_url_tasks}/tasks/stats", timeout=5)
            task_stats_time = time.time() - start_time
            
            if response.status_code != 200:
                self.log_result("Task Stats Performance", "FAILED", f"HTTP {response.status_code}")
                return False
            
            # Both should respond within 2 seconds
            max_response_time = 2.0
            
            if user_stats_time > max_response_time:
                self.log_result("User Stats Performance", "FAILED", f"Response time {user_stats_time:.2f}s exceeds {max_response_time}s")
                return False
            
            if task_stats_time > max_response_time:
                self.log_result("Task Stats Performance", "FAILED", f"Response time {task_stats_time:.2f}s exceeds {max_response_time}s")
                return False
            
            self.log_result("Statistics Performance", "PASSED", 
                          f"User stats: {user_stats_time:.2f}s, Task stats: {task_stats_time:.2f}s")
            
            print(f"⚡ Performance Summary:")
            print(f"   - User Stats Response Time: {user_stats_time:.2f} seconds")
            print(f"   - Task Stats Response Time: {task_stats_time:.2f} seconds")
            print(f"   - Both within acceptable limit of {max_response_time} seconds")
            
            return True
            
        except Exception as e:
            self.log_result("Statistics Performance", "FAILED", f"Exception: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== LIMPIEZA DE DATOS DE PRUEBA ===")
        cleanup_success = self.tracker.cleanup_all_data(self.base_url_users, self.base_url_tasks)
        
        if cleanup_success:
            print("✅ Limpieza de datos completada exitosamente")
            self.log_result("Test Data Cleanup", "PASSED", f"Cleaned {len(self.tracker.created_users)} users and {len(self.tracker.created_tasks)} tasks")
        else:
            print("❌ Error en la limpieza de datos")
            self.log_result("Test Data Cleanup", "FAILED", "Could not clean all test data")
        
        return cleanup_success
    
    def verify_cleanup(self):
        """Verify that test data was properly cleaned"""
        print("\n=== VERIFICACIÓN DE LIMPIEZA ===")
        verification_success = self.tracker.verify_cleanup(self.base_url_users, self.base_url_tasks)
        
        if verification_success:
            print("✅ Verificación de limpieza exitosa: Todos los datos de prueba fueron eliminados")
            self.log_result("Cleanup Verification", "PASSED", "All test data successfully removed")
        else:
            print("❌ Error en verificación de limpieza: Algunos datos de prueba aún existen")
            self.log_result("Cleanup Verification", "FAILED", "Some test data still exists in the system")
        
        return verification_success
    
    def generate_report(self):
        """Generate PDF report of test results"""
        print("\n=== GENERACIÓN DE REPORTE PDF ===")
        
        try:
            generator = PDFReportGenerator()
            
            # Prepare summary data
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
            failed_tests = total_tests - passed_tests
            
            summary_data = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'users_created': len(self.tracker.created_users),
                'tasks_created': len(self.tracker.created_tasks),
                'users_cleaned': len(self.tracker.created_users),
                'tasks_cleaned': len(self.tracker.created_tasks)
            }
            
            report_path = generator.generate_report(
                test_type="Statistics Integration Test",
                test_results=self.test_results,
                summary_data=summary_data
            )
            
            print(f"✅ Reporte PDF generado: {report_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando reporte PDF: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run the complete statistics integration test suite"""
        print("=" * 80)
        print("PRUEBA DE INTEGRACIÓN DE ESTADÍSTICAS DEL SISTEMA")
        print("=" * 80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Servicios bajo prueba:")
        print(f"  - User Service: {self.base_url_users}")
        print(f"  - Task Service: {self.base_url_tasks}")
        
        # Setup test data
        users, tasks = self.setup_test_data()
        
        if not users or not tasks:
            print("❌ Error en configuración de datos de prueba. Abortando.")
            return False
        
        # Run all tests
        tests_passed = 0
        total_tests = 5
        
        if self.test_user_stats_endpoint():
            tests_passed += 1
        
        if self.test_task_stats_endpoint():
            tests_passed += 1
        
        if self.test_cross_service_integration():
            tests_passed += 1
        
        if self.test_statistics_performance():
            tests_passed += 1
        
        # Cleanup and verify
        cleanup_success = self.cleanup_test_data()
        verify_success = self.verify_cleanup()
        
        if cleanup_success and verify_success:
            tests_passed += 1
        
        # Generate report
        self.generate_report()
        
        # Final summary
        print("\n" + "=" * 80)
        print("RESUMEN FINAL")
        print("=" * 80)
        print(f"Pruebas ejecutadas: {total_tests}")
        print(f"Pruebas exitosas: {tests_passed}")
        print(f"Pruebas fallidas: {total_tests - tests_passed}")
        print(f"Tasa de éxito: {(tests_passed / total_tests * 100):.1f}%")
        
        if tests_passed == total_tests:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
            return True
        else:
            print("⚠️  Algunas pruebas fallaron. Ver detalles arriba.")
            return False

def main():
    """Main function to run the statistics integration test"""
    try:
        test = StatsIntegrationTest()
        success = test.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal en la prueba: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()