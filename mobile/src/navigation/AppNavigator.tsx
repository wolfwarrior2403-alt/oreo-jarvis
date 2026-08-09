import React from 'react';
import {ActivityIndicator, StyleSheet, View} from 'react-native';
import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import HomeScreen from '@/screens/HomeScreen';
import HistoryScreen from '@/screens/HistoryScreen';
import SettingsScreen from '@/screens/SettingsScreen';
import ConfirmationScreen from '@/screens/ConfirmationScreen';
import PairingScreen from '@/screens/PairingScreen';
import {useAuth} from '@/context/AuthContext';

export type RootStackParamList = {
  Tabs: undefined;
  Home: undefined;
  Confirmation: {actionId: string; summary: string};
};

export type TabParamList = {
  Home: undefined;
  History: undefined;
  Settings: undefined;
};

const RootStack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

function Tabs() {
  return (
    <Tab.Navigator screenOptions={{headerShown: false}}>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="History" component={HistoryScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const {isPaired, isLoading} = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color="#6C5CE7" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isPaired ? (
        <RootStack.Navigator>
          <RootStack.Screen name="Tabs" component={Tabs} options={{headerShown: false}} />
          <RootStack.Screen
            name="Confirmation"
            component={ConfirmationScreen}
            options={{presentation: 'transparentModal', headerShown: false, animation: 'fade'}}
          />
        </RootStack.Navigator>
      ) : (
        <PairingScreen />
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loading: {flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0F0E17'},
});
