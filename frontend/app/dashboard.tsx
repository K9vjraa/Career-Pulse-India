import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ScrollView,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface CareerRoadmap {
  id: string;
  title: string;
  stream: string;
  description: string;
  steps: any[];
  estimated_duration: string;
  difficulty_level: string;
}

interface User {
  id: string;
  name: string;
  email: string;
  selected_stream?: string;
}

interface UserProgress {
  user_id: string;
  career_id: string;
  completed_steps: string[];
  progress_percentage: number;
}

const streamColors: Record<string, string> = {
  Science: '#4ECDC4',
  Commerce: '#FFD93D', 
  Arts: '#FF6B6B',
};

const difficultyColors: Record<string, string> = {
  'Beginner': '#4CAF50',
  'Intermediate': '#FF9800',
  'Advanced': '#F44336',
};

export default function DashboardScreen() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [roadmaps, setRoadmaps] = useState<CareerRoadmap[]>([]);
  const [userProgress, setUserProgress] = useState<UserProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      const token = await AsyncStorage.getItem('auth_token');
      
      if (!userData || !token) {
        router.replace('/auth/login');
        return;
      }

      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);

      if (!parsedUser.selected_stream) {
        router.replace('/stream-selection');
        return;
      }

      await fetchRoadmaps(parsedUser.selected_stream, token);
      await fetchUserProgress(token);
      
    } catch (error) {
      console.error('Initialization error:', error);
      Alert.alert('Error', 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoadmaps = async (stream: string, token: string) => {
    try {
      const response = await fetch(
        `${EXPO_PUBLIC_BACKEND_URL}/api/roadmaps?stream=${stream}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setRoadmaps(data);
      }
    } catch (error) {
      console.error('Error fetching roadmaps:', error);
    }
  };

  const fetchUserProgress = async (token: string) => {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/progress`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserProgress(data);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await initializeData();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await AsyncStorage.removeItem('auth_token');
            await AsyncStorage.removeItem('user_data');
            router.replace('/');
          },
        },
      ]
    );
  };

  const navigateToRoadmap = (roadmap: CareerRoadmap) => {
    router.push(`/roadmap/${roadmap.id}`);
  };

  const getProgressForRoadmap = (roadmapId: string): number => {
    const progress = userProgress.find(p => p.career_id === roadmapId);
    return progress?.progress_percentage || 0;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <LinearGradient
          colors={['#1a1a2e', '#16213e', '#0f3460']}
          style={styles.gradient}
        >
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#4ECDC4" />
            <Text style={styles.loadingText}>Loading your roadmaps...</Text>
          </View>
        </LinearGradient>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <LinearGradient
        colors={['#1a1a2e', '#16213e', '#0f3460']}
        style={styles.gradient}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.userInfo}>
              <Text style={styles.greeting}>Hello,</Text>
              <Text style={styles.userName}>{user?.name} 👋</Text>
              <Text style={styles.streamBadge}>
                {user?.selected_stream} Stream
              </Text>
            </View>
            
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={24} color="#FF6B6B" />
            </TouchableOpacity>
          </View>

          {/* Progress Overview */}
          <View style={styles.progressOverview}>
            <Text style={styles.sectionTitle}>Your Progress</Text>
            <View style={styles.statsContainer}>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>
                  {roadmaps.length}
                </Text>
                <Text style={styles.statLabel}>Total Careers</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>
                  {userProgress.filter(p => p.progress_percentage > 0).length}
                </Text>
                <Text style={styles.statLabel}>Started</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statNumber}>
                  {userProgress.filter(p => p.progress_percentage === 100).length}
                </Text>
                <Text style={styles.statLabel}>Completed</Text>
              </View>
            </View>
          </View>

          {/* Career Roadmaps */}
          <View style={styles.roadmapsSection}>
            <Text style={styles.sectionTitle}>Career Roadmaps</Text>
            
            <View style={styles.roadmapsList}>
              {roadmaps.map((roadmap) => {
                const progress = getProgressForRoadmap(roadmap.id);
                const streamColor = streamColors[roadmap.stream] || '#4ECDC4';
                
                return (
                  <TouchableOpacity
                    key={roadmap.id}
                    style={styles.roadmapCard}
                    onPress={() => navigateToRoadmap(roadmap)}
                    activeOpacity={0.8}
                  >
                    <LinearGradient
                      colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                      style={styles.cardGradient}
                    >
                      <View style={styles.cardHeader}>
                        <View style={styles.cardTitleContainer}>
                          <Text style={styles.cardTitle}>{roadmap.title}</Text>
                          <View style={styles.cardMeta}>
                            <View style={[styles.difficultyBadge, { backgroundColor: difficultyColors[roadmap.difficulty_level] + '20' }]}>
                              <Text style={[styles.difficultyText, { color: difficultyColors[roadmap.difficulty_level] }]}>
                                {roadmap.difficulty_level}
                              </Text>
                            </View>
                            <Text style={styles.duration}>{roadmap.estimated_duration}</Text>
                          </View>
                        </View>
                        <Ionicons name="arrow-forward-circle" size={24} color={streamColor} />
                      </View>
                      
                      <Text style={styles.cardDescription}>
                        {roadmap.description}
                      </Text>
                      
                      <View style={styles.progressContainer}>
                        <View style={styles.progressInfo}>
                          <Text style={styles.progressLabel}>Progress</Text>
                          <Text style={styles.progressPercent}>{Math.round(progress)}%</Text>
                        </View>
                        <View style={styles.progressBarContainer}>
                          <View style={[styles.progressBar, { backgroundColor: streamColor + '20' }]}>
                            <View 
                              style={[
                                styles.progressFill,
                                { 
                                  width: `${progress}%`,
                                  backgroundColor: streamColor
                                }
                              ]} 
                            />
                          </View>
                        </View>
                      </View>
                      
                      <View style={styles.stepsInfo}>
                        <Ionicons name="list-outline" size={16} color="rgba(255, 255, 255, 0.6)" />
                        <Text style={styles.stepsText}>
                          {roadmap.steps.length} steps
                        </Text>
                      </View>
                    </LinearGradient>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
          
          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <View style={styles.actionsGrid}>
              <TouchableOpacity 
                style={styles.actionCard}
                onPress={() => router.push('/stream-selection')}
              >
                <Ionicons name="swap-horizontal" size={24} color="#FFD93D" />
                <Text style={styles.actionText}>Change Stream</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.actionCard}>
                <Ionicons name="analytics-outline" size={24} color="#4ECDC4" />
                <Text style={styles.actionText}>View Analytics</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 24,
  },
  userInfo: {
    flex: 1,
  },
  greeting: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginTop: 4,
  },
  streamBadge: {
    fontSize: 12,
    color: '#4ECDC4',
    backgroundColor: 'rgba(78, 205, 196, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  logoutButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressOverview: {
    paddingHorizontal: 24,
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    paddingVertical: 20,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: '#4ECDC4',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 4,
  },
  roadmapsSection: {
    paddingHorizontal: 24,
    marginBottom: 32,
  },
  roadmapsList: {
    gap: 16,
  },
  roadmapCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  cardGradient: {
    padding: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  cardTitleContainer: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: '600',
  },
  duration: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  cardDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 20,
    marginBottom: 16,
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  progressPercent: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4ECDC4',
  },
  progressBarContainer: {
    height: 6,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  stepsInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  stepsText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  quickActions: {
    paddingHorizontal: 24,
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: 16,
  },
  actionCard: {
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 16,
    paddingVertical: 20,
    alignItems: 'center',
    gap: 8,
  },
  actionText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '500',
  },
});