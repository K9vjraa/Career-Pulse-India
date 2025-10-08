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
  Dimensions,
  Linking,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');
const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface RoadmapStep {
  id: string;
  title: string;
  description: string;
  resources: string[];
  duration: string;
}

interface CareerRoadmap {
  id: string;
  title: string;
  stream: string;
  description: string;
  steps: RoadmapStep[];
  estimated_duration: string;
  difficulty_level: string;
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

export default function RoadmapDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [roadmap, setRoadmap] = useState<CareerRoadmap | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingStep, setUpdatingStep] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchRoadmapData();
    }
  }, [id]);

  const fetchRoadmapData = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        router.replace('/auth/login');
        return;
      }

      // Fetch roadmap details
      const roadmapResponse = await fetch(
        `${EXPO_PUBLIC_BACKEND_URL}/api/roadmaps/${id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (roadmapResponse.ok) {
        const roadmapData = await roadmapResponse.json();
        setRoadmap(roadmapData);
      }

      // Fetch user progress
      const progressResponse = await fetch(
        `${EXPO_PUBLIC_BACKEND_URL}/api/progress/${id}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (progressResponse.ok) {
        const progressData = await progressResponse.json();
        setUserProgress(progressData);
      }

    } catch (error) {
      console.error('Error fetching roadmap data:', error);
      Alert.alert('Error', 'Failed to load roadmap data');
    } finally {
      setLoading(false);
    }
  };

  const toggleStepCompletion = async (stepId: string, completed: boolean) => {
    setUpdatingStep(stepId);
    
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        return;
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          career_id: id,
          step_id: stepId,
          completed: completed,
        }),
      });

      if (response.ok) {
        // Update local progress
        if (userProgress) {
          const updatedSteps = completed
            ? [...userProgress.completed_steps, stepId]
            : userProgress.completed_steps.filter(s => s !== stepId);
          
          const totalSteps = roadmap?.steps.length || 0;
          const newProgress = (updatedSteps.length / totalSteps) * 100;
          
          setUserProgress({
            ...userProgress,
            completed_steps: updatedSteps,
            progress_percentage: newProgress,
          });
        }
      } else {
        Alert.alert('Error', 'Failed to update progress');
      }
    } catch (error) {
      console.error('Error updating progress:', error);
      Alert.alert('Error', 'Network error occurred');
    } finally {
      setUpdatingStep(null);
    }
  };

  const openResource = async (url: string) => {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    } else {
      Alert.alert('Error', 'Cannot open this resource');
    }
  };

  const isStepCompleted = (stepId: string): boolean => {
    return userProgress?.completed_steps.includes(stepId) || false;
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
            <Text style={styles.loadingText}>Loading roadmap...</Text>
          </View>
        </LinearGradient>
      </SafeAreaView>
    );
  }

  if (!roadmap) {
    return (
      <SafeAreaView style={styles.container}>
        <LinearGradient
          colors={['#1a1a2e', '#16213e', '#0f3460']}
          style={styles.gradient}
        >
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={64} color="#FF6B6B" />
            <Text style={styles.errorText}>Roadmap not found</Text>
            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
              <Text style={styles.backButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        </LinearGradient>
      </SafeAreaView>
    );
  }

  const streamColor = streamColors[roadmap.stream] || '#4ECDC4';
  const completedSteps = userProgress?.completed_steps.length || 0;
  const totalSteps = roadmap.steps.length;
  const progressPercentage = userProgress?.progress_percentage || 0;

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
        >
          
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity 
              style={styles.headerBackButton} 
              onPress={() => router.back()}
            >
              <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
            </TouchableOpacity>
            <View style={styles.headerTitleContainer}>
              <Text style={styles.headerTitle}>Roadmap</Text>
            </View>
            <View style={styles.headerPlaceholder} />
          </View>

          {/* Roadmap Header */}
          <View style={styles.roadmapHeader}>
            <Text style={styles.roadmapTitle}>{roadmap.title}</Text>
            <Text style={styles.roadmapDescription}>{roadmap.description}</Text>
            
            <View style={styles.roadmapMeta}>
              <View style={styles.metaItem}>
                <Ionicons name="school-outline" size={16} color={streamColor} />
                <Text style={[styles.metaText, { color: streamColor }]}>{roadmap.stream}</Text>
              </View>
              <View style={styles.metaItem}>
                <Ionicons name="time-outline" size={16} color="rgba(255, 255, 255, 0.6)" />
                <Text style={styles.metaText}>{roadmap.estimated_duration}</Text>
              </View>
              <View style={[styles.difficultyBadge, { backgroundColor: difficultyColors[roadmap.difficulty_level] + '20' }]}>
                <Text style={[styles.difficultyText, { color: difficultyColors[roadmap.difficulty_level] }]}>
                  {roadmap.difficulty_level}
                </Text>
              </View>
            </View>
          </View>

          {/* Progress Overview */}
          <View style={styles.progressSection}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressTitle}>Your Progress</Text>
              <Text style={styles.progressStats}>
                {completedSteps}/{totalSteps} steps completed
              </Text>
            </View>
            
            <View style={styles.progressBarContainer}>
              <LinearGradient
                colors={[streamColor + '40', streamColor + '20']}
                style={styles.progressBarBackground}
              >
                <LinearGradient
                  colors={[streamColor, streamColor + 'CC']}
                  style={[styles.progressBarFill, { width: `${progressPercentage}%` }]}
                />
              </LinearGradient>
              <Text style={[styles.progressPercentage, { color: streamColor }]}>
                {Math.round(progressPercentage)}%
              </Text>
            </View>
          </View>

          {/* Roadmap Steps */}
          <View style={styles.stepsSection}>
            <Text style={styles.stepsTitle}>Roadmap Steps</Text>
            
            <View style={styles.stepsList}>
              {roadmap.steps.map((step, index) => {
                const completed = isStepCompleted(step.id);
                const isUpdating = updatingStep === step.id;
                
                return (
                  <View key={step.id} style={styles.stepItem}>
                    {/* Connection Line */}
                    {index < roadmap.steps.length - 1 && (
                      <View 
                        style={[
                          styles.connectionLine,
                          { backgroundColor: completed ? streamColor : 'rgba(255, 255, 255, 0.2)' }
                        ]} 
                      />
                    )}
                    
                    {/* Step Card */}
                    <View style={[styles.stepCard, completed && styles.completedCard]}>
                      <LinearGradient
                        colors={
                          completed 
                            ? [streamColor + '20', streamColor + '10']
                            : ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']
                        }
                        style={styles.stepCardGradient}
                      >
                        
                        {/* Step Header */}
                        <View style={styles.stepHeader}>
                          <View style={styles.stepNumber}>
                            <View 
                              style={[
                                styles.stepCircle,
                                { 
                                  backgroundColor: completed ? streamColor : 'rgba(255, 255, 255, 0.2)',
                                  borderColor: completed ? streamColor : 'rgba(255, 255, 255, 0.3)'
                                }
                              ]}
                            >
                              {completed ? (
                                <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                              ) : (
                                <Text style={[styles.stepNumberText, { color: completed ? '#FFFFFF' : 'rgba(255, 255, 255, 0.8)' }]}>
                                  {index + 1}
                                </Text>
                              )}
                            </View>
                          </View>
                          
                          <View style={styles.stepContent}>
                            <Text style={[styles.stepTitle, completed && styles.completedStepTitle]}>
                              {step.title}
                            </Text>
                            <Text style={styles.stepDuration}>{step.duration}</Text>
                          </View>
                          
                          <TouchableOpacity
                            style={styles.checkboxContainer}
                            onPress={() => toggleStepCompletion(step.id, !completed)}
                            disabled={isUpdating}
                          >
                            {isUpdating ? (
                              <ActivityIndicator size="small" color={streamColor} />
                            ) : (
                              <View 
                                style={[
                                  styles.checkbox,
                                  { 
                                    backgroundColor: completed ? streamColor : 'transparent',
                                    borderColor: completed ? streamColor : 'rgba(255, 255, 255, 0.3)'
                                  }
                                ]}
                              >
                                {completed && (
                                  <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                                )}
                              </View>
                            )}
                          </TouchableOpacity>
                        </View>
                        
                        {/* Step Description */}
                        <Text style={styles.stepDescription}>
                          {step.description}
                        </Text>
                        
                        {/* Resources */}
                        {step.resources && step.resources.length > 0 && (
                          <View style={styles.resourcesContainer}>
                            <Text style={styles.resourcesTitle}>Resources:</Text>
                            <View style={styles.resourcesList}>
                              {step.resources.map((resource, resourceIndex) => (
                                <TouchableOpacity
                                  key={resourceIndex}
                                  style={styles.resourceItem}
                                  onPress={() => openResource(resource)}
                                >
                                  <Ionicons name="link-outline" size={14} color={streamColor} />
                                  <Text 
                                    style={[styles.resourceText, { color: streamColor }]}
                                    numberOfLines={1}
                                  >
                                    {resource.replace(/https?:\/\//, '')}
                                  </Text>
                                </TouchableOpacity>
                              ))}
                            </View>
                          </View>
                        )}
                      </LinearGradient>
                    </View>
                  </View>
                );
              })}
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorText: {
    fontSize: 18,
    color: '#FF6B6B',
    marginTop: 16,
    marginBottom: 32,
  },
  backButton: {
    backgroundColor: '#4ECDC4',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 20,
    paddingBottom: 24,
  },
  headerBackButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  headerPlaceholder: {
    width: 40,
  },
  roadmapHeader: {
    paddingHorizontal: 24,
    marginBottom: 32,
  },
  roadmapTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  roadmapDescription: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 24,
    marginBottom: 20,
  },
  roadmapMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  difficultyBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
  },
  progressSection: {
    paddingHorizontal: 24,
    marginBottom: 32,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  progressStats: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  progressBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  progressBarBackground: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressPercentage: {
    fontSize: 16,
    fontWeight: '600',
    minWidth: 40,
    textAlign: 'right',
  },
  stepsSection: {
    paddingHorizontal: 24,
  },
  stepsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 20,
  },
  stepsList: {
    gap: 0,
  },
  stepItem: {
    position: 'relative',
    marginBottom: 20,
  },
  connectionLine: {
    position: 'absolute',
    left: 20,
    top: 60,
    width: 2,
    height: 20,
    zIndex: 0,
  },
  stepCard: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  completedCard: {
    borderColor: 'rgba(78, 205, 196, 0.3)',
  },
  stepCardGradient: {
    padding: 20,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  stepNumber: {
    marginRight: 16,
  },
  stepCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
  },
  stepNumberText: {
    fontSize: 16,
    fontWeight: '600',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  completedStepTitle: {
    color: '#4ECDC4',
  },
  stepDuration: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  checkboxContainer: {
    padding: 4,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 20,
    marginBottom: 16,
  },
  resourcesContainer: {
    marginTop: 8,
  },
  resourcesTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4ECDC4',
    marginBottom: 8,
  },
  resourcesList: {
    gap: 6,
  },
  resourceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 4,
  },
  resourceText: {
    fontSize: 12,
    flex: 1,
  },
});